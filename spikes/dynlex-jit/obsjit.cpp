// The JIT seam: compiles a DynLex script to an object with the dynlex
// compiler, loads it in-process with ORC and calls its entry on the model.
#include "llvm/ExecutionEngine/Orc/LLJIT.h"
#include "llvm/ExecutionEngine/Orc/ExecutionUtils.h"
#include "llvm/Support/MemoryBuffer.h"
#include "llvm/Support/TargetSelect.h"
#include <chrono>
#include <cstdio>
#include <cstdlib>
#include <memory>
#include <string>

using namespace llvm;
using namespace llvm::orc;

static std::unique_ptr<LLJIT> jit;
static int scriptCount = 0;

static bool ensureJit() {
	if (jit) return true;
	InitializeNativeTarget();
	InitializeNativeTargetAsmPrinter();
	auto created = LLJITBuilder().create();
	if (!created) { logAllUnhandledErrors(created.takeError(), errs(), "obsjit: "); return false; }
	jit = std::move(*created);
	// Scripts resolve libc (malloc, realloc, free, printf) from the editor's process.
	jit->getMainJITDylib().addGenerator(cantFail(
		DynamicLibrarySearchGenerator::GetForCurrentProcess(jit->getDataLayout().getGlobalPrefix())));
	return true;
}

// Returns the entry's 64-bit result, or -1 when compiling or loading fails.
extern "C" long long obs_jit_run_script(const char *scriptPath, const char *entrySymbol, void *model) {
	if (!ensureJit()) return -1;
	using ms = std::chrono::duration<double, std::milli>;
	auto start = std::chrono::steady_clock::now();
	std::string object = std::string(scriptPath) + ".o";
	const char *dynlex = std::getenv("DYNLEX");
	std::string command = std::string(dynlex ? dynlex : "dynlex") + " '" + scriptPath + "' --emit-object --no-main -O1 -o '" + object + "'";
	if (std::system(command.c_str()) != 0) { std::fprintf(stderr, "obsjit: compile failed\n"); return -1; }
	auto compiled = std::chrono::steady_clock::now();
	auto &session = jit->getExecutionSession();
	auto library = session.createJITDylib("script" + std::to_string(++scriptCount));
	if (!library) { logAllUnhandledErrors(library.takeError(), errs(), "obsjit: "); return -1; }
	library->addToLinkOrder(jit->getMainJITDylib());
	auto buffer = MemoryBuffer::getFile(object);
	if (!buffer) { std::fprintf(stderr, "obsjit: no object\n"); return -1; }
	if (auto error = jit->addObjectFile(*library, std::move(*buffer))) { logAllUnhandledErrors(std::move(error), errs(), "obsjit: "); return -1; }
	auto entry = jit->lookup(*library, entrySymbol);
	if (!entry) { logAllUnhandledErrors(entry.takeError(), errs(), "obsjit: "); return -1; }
	long long result = entry->toPtr<long long (*)(void *)>()(model);
	auto done = std::chrono::steady_clock::now();
	std::fprintf(stderr, "obsjit: compile %.0f ms, load+run %.1f ms\n", ms(compiled - start).count(), ms(done - compiled).count());
	return result;
}

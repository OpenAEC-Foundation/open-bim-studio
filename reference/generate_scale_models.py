"""Generate N unit boxes on a square grid as OBJ. Measures scaling, not geometry."""
import argparse, math

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--count", type=int, required=True)
    p.add_argument("--out", required=True)
    a = p.parse_args()
    side = math.ceil(math.sqrt(a.count))
    with open(a.out, "w", encoding="utf-8") as f:
        for i in range(a.count):
            x, y = (i % side) * 2.0, (i // side) * 2.0
            for dx, dy, dz in [(0,0,0),(1,0,0),(1,1,0),(0,1,0),(0,0,1),(1,0,1),(1,1,1),(0,1,1)]:
                f.write(f"v {x+dx} {y+dy} {dz}\n")
            b = 8 * i + 1
            for q in [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]:
                f.write("f " + " ".join(str(b + k) for k in q) + "\n")

if __name__ == "__main__":
    main()

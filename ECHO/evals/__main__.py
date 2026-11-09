import argparse,json
from pathlib import Path
from .schemas import read,write_new
from .dataset_validator import validate
def main():
    p=argparse.ArgumentParser(description="ECHO 独立评测入口")
    sub=p.add_subparsers(dest="command",required=True)
    v=sub.add_parser("validate-dataset");v.add_argument("dataset");v.add_argument("--require-gold",action="store_true")
    r=sub.add_parser("run");r.add_argument("dataset");r.add_argument("--parent-run")
    for name in ("annotate","score","export"):
        c=sub.add_parser(name);c.add_argument("run")
        if name=="annotate":c.add_argument("--output",required=True)
        else:c.add_argument("--review")
    c=sub.add_parser("compare");c.add_argument("first");c.add_argument("second");c.add_argument("--first-review");c.add_argument("--second-review")
    args=p.parse_args()
    if args.command=="validate-dataset":print(json.dumps(validate(read(args.dataset),args.require_gold),ensure_ascii=False,indent=2))
    elif args.command=="run":
        from .runner import run
        run(args.dataset,parent=args.parent_run)
    else:
        from .reporter import review_template,score,export,compare
        if args.command=="annotate":write_new(args.output,review_template(args.run));print(args.output)
        elif args.command=="score":print(json.dumps(score(args.run,args.review),ensure_ascii=False,indent=2))
        elif args.command=="export":export(args.run,args.review)
        else:print(json.dumps(compare(args.first,args.second,args.first_review,args.second_review),ensure_ascii=False,indent=2))
if __name__=="__main__":main()


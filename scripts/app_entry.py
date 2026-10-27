from multiprocessing import freeze_support
import sys

if __name__=='__main__':
    freeze_support()
    args=sys.argv[1:]
    if args[:1]==['--worker']:
        from fonesi_edit.worker import main
        raise SystemExit(main(args[1:]))
    if args[:1]==['--verify']:
        from fonesi_edit.verification import main
        raise SystemExit(main(args[1:]))
    from fonesi_edit.app import main
    raise SystemExit(main(args))

"""Kiểm bốn model selected và chuẩn bị epoch plan refit, CPU-only."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))
from knowledge_tracing.akt.research_junyi_engineering import file_sha, write_json
from knowledge_tracing.akt.research_junyi_selection import load_full_selected_cache
from knowledge_tracing.akt.research_junyi_refit import make_epoch_plan, refit_view


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('a0', 'a1', 'a2', 'a3', 'cache', 'roles', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--cache-sha256', required=True)
    parser.add_argument('--roles-sha256', required=True)
    args = parser.parse_args()
    destination = args.output.resolve()
    if not destination.is_relative_to(ROOT / 'research_tracking/runs') or destination.exists():
        raise ValueError('Exclusive owned run output required')
    inputs = load_full_selected_cache(args.cache, args.roles,
        expected_manifest_sha256=args.cache_sha256, expected_roles_sha256=args.roles_sha256)
    indices, inventory = {}, {}
    for variant in ('A0', 'A1', 'A2', 'A3'):
        path = getattr(args, variant.lower()).resolve()
        if not path.is_relative_to(ROOT / 'experiments/akt/results'):
            raise ValueError('Owned selected export required')
        index = json.loads(path.read_text(encoding='utf-8'))
        checkpoint = path.parent / index['checkpoint_file']
        if (checkpoint.parent.resolve() != path.parent or file_sha(checkpoint) != index['checkpoint_sha256']
                or checkpoint.stat().st_size != index['checkpoint_bytes']):
            raise ValueError('Selected export checkpoint changed')
        for source in (path, checkpoint):
            inventory[source.relative_to(ROOT).as_posix()] = dict(bytes=source.stat().st_size, sha256=file_sha(source))
        indices[variant] = index
    plan = make_epoch_plan(indices, roles_identity=inputs.train.roles.identity)
    if plan['selected_inputs_identity'] != inputs.identity:
        raise ValueError('Exported selected models and dataset cache differ')
    refit = refit_view(inputs)
    write_json(destination, plan)
    write_json(destination.with_suffix('.receipt.json'), dict(status='EPOCH_PLAN_PREPARED_NO_TRAINING_AUTHORITY',
        plan_sha256=file_sha(destination), plan_identity=plan['identity'], input_inventory=inventory,
        refit_learners=len(refit.view.users), refit_targets_per_epoch=refit.targets,
        epochs={key:value['epochs'] for key,value in plan['candidates'].items()},
        training_performed=False, cloud_spending_usd=0))
    print(json.dumps(dict(status='EPOCH_PLAN_PREPARED', targets=refit.targets,
                          learners=len(refit.view.users), epochs={key:value['epochs'] for key,value in plan['candidates'].items()})))


if __name__ == '__main__':
    main()

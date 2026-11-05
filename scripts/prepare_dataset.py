"""Create reproducible manifests without modifying the source images.

Run from the project root: python scripts/prepare_dataset.py
Only the supplied original-image collection should be placed in data/raw.
"""
import csv
import hashlib
import json
import random
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PREFIXES = {
    'bacterial_leaf_blight': 'bacterial_leaf_blight',
    'brown_spot': 'brown_spot',
    'healthy_rice_leaf': 'healthy',
    'leaf_blast': 'leaf_blast',
}


def main():
    files = sorted((ROOT / 'data/raw').rglob('*'))
    inventory = Counter()
    groups = defaultdict(list)
    for path in files:
        if not path.is_file() or path.suffix.lower() not in {'.jpg', '.jpeg', '.png'}:
            continue
        inventory[path.parent.name] += 1
        normalized = path.stem.lower().replace(' ', '')
        label = next((value for prefix, value in PREFIXES.items()
                      if normalized.startswith(prefix + '(')), None)
        if label is None:
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        groups[digest].append((label, path.relative_to(ROOT).as_posix()))

    conflicts = []
    by_class = defaultdict(list)
    duplicates = []
    for digest, entries in sorted(groups.items()):
        if len({label for label, _ in entries}) != 1:
            conflicts.append({'sha256': digest, 'images': entries})
            continue
        label, source = entries[0]
        by_class[label].append({'path': source, 'label': label, 'sha256': digest})
        duplicates.extend({'kept': source, 'excluded': path} for _, path in entries[1:])
    if set(by_class) != set(PREFIXES.values()):
        raise ValueError(f'Missing expected classes; found {sorted(by_class)}')

    output = ROOT / 'data/processed'
    output.mkdir(parents=True, exist_ok=True)
    rows = []
    counts = {}
    for label, images in sorted(by_class.items()):
        random.Random(42).shuffle(images)
        n_train = int(len(images) * .70)
        n_val = int(len(images) * .15)
        counts[label] = {}
        for split, subset in [('train', images[:n_train]),
                              ('validation', images[n_train:n_train+n_val]),
                              ('test', images[n_train+n_val:])]:
            counts[label][split] = len(subset)
            rows.extend(dict(image, split=split) for image in subset)
    # Check that identical file contents cannot appear across split boundaries.
    assert len({row['sha256'] for row in rows}) == len(rows)
    with (output / 'manifest.csv').open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=['path', 'label', 'sha256', 'split'])
        writer.writeheader()
        writer.writerows(rows)
    report = {
        'seed': 42, 'source_inventory': dict(inventory), 'counts': counts,
        'selected_unique_images': len(rows), 'exact_duplicates_excluded': duplicates,
        'conflicting_label_groups_excluded': conflicts,
        'limitations': [
            'File hashes detect exact duplicates only; near duplicates need visual review.',
            'No plant, farm, or session identifiers were supplied; this is a provisional image-level split.',
            'Image decoding and disease labels have not been validated.',
            'Confirm that the supplied collection contains originals, not augmented variants.'
        ]
    }
    (output / 'report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({key: value for key, value in report.items()
                      if key not in {'exact_duplicates_excluded', 'conflicting_label_groups_excluded'}}, indent=2))
    print(f'Exact duplicates excluded: {len(duplicates)}')
    print(f'Conflicting label groups excluded: {len(conflicts)}')


if __name__ == '__main__':
    main()

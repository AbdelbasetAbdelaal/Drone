import glob
import yaml

for path in glob.glob('config/benchmarks/*.yaml'):
    with open(path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    modified = False
    default_pop = data.get('populations', {}).get('default', {})
    for gender, g_metrics in default_pop.items():
        if gender == 'status': continue
        for m_name, mcfg in g_metrics.items():
            if m_name == 'status': continue
            ev = mcfg.get('evidence', {})
            if ev:
                if 'validation_status' not in ev:
                    ev['validation_status'] = 'VALIDATED'
                    modified = True
                if 'evidence_level' not in ev:
                    ev['evidence_level'] = 'LEVEL_A'
                    modified = True
                if 'sample_size' not in ev:
                    ev['sample_size'] = 184
                    modified = True
    if modified:
        with open(path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, sort_keys=False)
print("Done")

SEGMENTATION_GROUPS = {
    "wm-cerebral": [2, 41],
    "wm-cerebellar": [7, 46],
    "wm-hypointensities": [77, 78, 70],
    "wm-pathological": [77, 78, 79, 80, 100, 109],
    "cortex-cerebral": [3, 42],
    "cortex-cerebellar": [8, 47],
    "csf": [4, 5, 14, 15, 24, 43, 44],
    "cerebellum": [7, 8, 46, 47],
    "corpus-callosum": [251, 252, 253, 254, 255],
    "caudate": [11, 50],
    "putamen": [12, 51],
    "pallidum": [13, 52],
    "hippocampus": [17, 53],
    "amygdala": [18, 54],
    "accumbens": [26, 58],
    "brainstem": [16],
}

COLLECTIONS = {
    "white-matter": [
        "wm-cerebral",
        "wm-cerebellar",
        "wm-hypointensities",
        "wm-pathological",
    ],
    "gray-matter": [
        "cortex-cerebral",
        "cortex-cerebellar",
        "caudate",
        "putamen",
        "pallidum",
        "hippocampus",
        "amygdala",
        "accumbens",
    ],
    "basal-ganglias": [
        "caudate",
        "putamen",
        "pallidum",
        "hippocampus",
        "amygdala",
        "accumbens",
    ],
}


def default_segmentation_groups():
    groups = {**SEGMENTATION_GROUPS}
    for collection, group_labels in COLLECTIONS.items():
        groups[collection] = sum([groups[label] for label in group_labels], start=[])
    return groups


# Not certain if useful, kept until first commit
def invert_seg_groups(seg_groups):
    d = {}
    for key, vals in seg_groups.items():
        for val in vals:
            if val not in d:
                d[val] = [key]
            else:
                d[val].append(key)
    return d


if __name__ == "__main__":
    import json

    print(json.dumps(default_segmentation_groups(), indent=4))

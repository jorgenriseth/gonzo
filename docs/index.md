# Gonzo Documentation

Welcome to the documentation for the **Gonzo** dataset: Human brain MRI data of
CSF-tracer evolution over 72h for data-integrated simulations.

## Overview

This documentation provides guidance for how to download the Gonzo dataset. It
also provides instructions for reproducing the processed data from the raw
images, by executing the processing pipeline from start-to-finish with
`snakemake`, or how you could execute most of the individual steps of the
processing pipeline.

This documentation covers:

- **Setup and Installation**: Step-by-step guide to install dependencies and set
  up the processing environment.
- **Data Download**: Downloading the data with a script leveraging the Zenodo
- **Processing Pipeline**: Complete Snakemake workflow for reproducible data
  processing.
- **Concise workflow examples**: Guides on the shell commands required to run
  key parts of the processing pipeline.
- **Technical guides (Unpolished)**: A more technical description of some of the
  processing steps, such as Look-Locker T1-mapping or normalization of
  T1-weighted images. Most of these are mainly included for transparency, and
  have not been polished before publication.
- **Visualization (Unpolished)**: MRI visualization tools and analysis
  notebooks. These notebooks were mainly used to generate the figure for the
  article, and might not be of large interest.

## Getting Started

Start with the [Setup Guide](gonzo-readme-setup.ipynb) to download the data, or
to configure your environment and executing the processing pipeline. Then use
the sidebar to navigate to topics of interest.

## Dataset Information

- **Data Record**: <https://doi.org/10.1101/2025.07.23.25331971>
- **Data Descriptor**: <https://doi.org/10.5281/zenodo.14266867>
- **GitHub Repository**: <https://github.com/jorgenriseth/gonzo>

## Citation

If you use this data or processing pipeline in your research, please cite:

```bibtex
@article{riseth2025human,
  title={Human brain MRI data of CSF tracer evolution over 72h for data-integrated simulations},
  author={Riseth, J{\o}rgen N and Koch, Timo and Lian, Sofie Lysholm and Stor{\aa}s, Tryggve Holck and Zikatanov, Ludmil T and Valnes, Lars Magnus and Nordengen, Kaja and Mardal, Kent-Andr{\'e}},
  journal={medRxiv},
  pages={2025--07},
  year={2025},
  publisher={Cold Spring Harbor Laboratory Press}
}
```

## Code Authors

- Jørgen Riseth
- Timo Koch

## License

See the
[LICENSE](https://github.com/jorgenriseth/gonzo/blob/prepublication-patches/LICENSE)
file in the repository for details.

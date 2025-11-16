# Gonzo Documentation

Welcome to the documentation for the **Gonzo** project: Human brain MRI data of CSF-tracer evolution over 72h for data-integrated simulations.

## Overview

This documentation provides comprehensive guides and tutorials for processing and analyzing dynamic contrast-enhanced MRI images following intrathecal injection of gadobutrol in a healthy human subject.

## Dataset Information

- **Data Record**: <https://doi.org/10.1101/2025.07.23.25331971>
- **Data Descriptor**: <https://doi.org/10.5281/zenodo.14266867>
- **GitHub Repository**: <https://github.com/jorgenriseth/gonzo>

## What's Included

This documentation covers:

- **Setup and Installation**: Step-by-step guide to install dependencies and set up the processing environment
- **Data Extraction**: DICOM data extraction and conversion workflows
- **T1 Mapping**: Look-Locker and mixed sequence T1 map generation and validation
- **Contrast Analysis**: Tracer concentration estimation and signal normalization
- **Visualization**: MRI visualization tools and analysis notebooks
- **Processing Pipeline**: Complete Snakemake workflow for reproducible data processing

## Getting Started

If you're new to this project, start with the [Setup Guide](gonzo-readme-setup.ipynb) to configure your environment.

If you're only interested in downloading the processed data, refer to the download instructions in the setup guide.

## Citation

If you use this data or processing pipeline in your research, please cite:

```bibtex
@article{gonzo2025,
  title={Human brain MRI data of CSF-tracer evolution over 72h for data-integrated simulations},
  author={Riseth, Jørgen and Koch, Timo},
  year={2025},
  doi={10.1101/2025.07.23.25331971}
}
```

## Authors

- Jørgen Riseth
- Timo Koch

## License

See the [LICENSE](https://github.com/jorgenriseth/gonzo/blob/prepublication-patches/LICENSE) file in the repository for details.

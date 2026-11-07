# Gonzo: Human brain MRI data of CSF-tracer evolution over 72h for data-integrated simulations

This repository contains the processing pipeline for the Gonzo dataset: dynamic contrast-enhanced MRI images following intrathecal injection of gadobutrol in a healthy human volunteer.

## Resources

- **📚 Documentation**: https://jorgenriseth.github.io/gonzo
- **📊 Data Record**: https://doi.org/10.1101/2025.07.23.25331971
- **📝 Data Descriptor**: https://doi.org/10.5281/zenodo.14266867

## Quick Start

The pipeline environment and tasks are defined in [pixi.toml](pixi.toml),
separately from the Python package metadata.

The build/environment migration is staged locally. See
[release environment preparation](docs/environment-release.md) for standalone
release and editable-development routes, validation gates, and container builds.

For detailed instructions on data download, setup, and running the pipeline, please visit the [documentation](https://jorgenriseth.github.io/gonzo).

## Citation

If you use this data or processing pipeline in your research, please cite

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

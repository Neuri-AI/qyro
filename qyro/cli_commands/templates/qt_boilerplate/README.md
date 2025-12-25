# Qyro App

This application is built using [Qyro](https://qyro.neuri.ai/), a modern **Python-based application library** for building **desktop and mobile applications** using native and web technologies as a rendering layer.

Qyro is **not a traditional library**. It provides a local runtime that powers native-like applications, including:

- Desktop apps (Windows, macOS, Linux)
- Mobile apps (iOS, Android)
- Packaging and installer generation


## Installation

```bash
poetry install
```

This installs all the required dependencies for the application.

## Run application

```bash
qyro start
```

This command starts the **local application runtime** and launches the app window.

## Build (debug)

```bash
qyro freeze
```

This command builds the application into the `build/` directory for debugging and testing purposes.


## Build (production)

```bash
qyro freeze --profile production
```

This command creates an optimized production build of the application.

## Package application

```bash
qyro package
```

This command generates **platform-specific installers** for your application
(e.g. `.exe`, `.dmg`, `.AppImage`, mobile packages, depending on target).


## License

This project is licensed under the MIT License.
See the [LICENSE](LICENSE) file for details.


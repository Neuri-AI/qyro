# Aplicaciones de ejemplo

Estos archivos pertenecen a la documentación española de Qyro. No contienen credenciales reales. `settings/secrets.json` es `{}` para satisfacer el primer build sin protección completa.

Desde esta carpeta, con Qyro CLI, Engine y PySide6 instalados mediante pip en el entorno activo:

```bash
qyro start
```

La demo principal es `pyside6_app.py`: abre una ventana, carga settings, selecciona un texto por plataforma y monta un componente Qt con estilos y contador. Los otros scripts utilizan PyQt6, PyQt5, PySide2, Tkinter o Kivy. Instala su toolkit con pip y selecciona el binding y entry point correspondientes antes de ejecutarlos con el CLI.

Para ejecutar mediante CLI, cambia `binding` y `entry_point` en `settings/base.json` al toolkit y script elegidos, y ejecuta `python -m qyro_cli start`. No basta cambiar el entry point para construir otro binding: los hooks de build utilizan la configuración.

`pydux_tkinter_app.py` y `pydux_pyside6_app.py` requieren instalar Pydux por separado. Pydux es una librería independiente y opcional, ajena al core del Engine y del CLI. Ambos ejemplos cancelan las suscripciones en el cierre nativo y deshabilitan DevTools.

El build inicial recomendado es `python -m qyro_cli build --mode onedir --debug`; requiere el extra `desktop` del CLI y compilador C. El `build.json` suministrado deshabilita optimizaciones agresivas. Después prueba el ejecutable desde otra carpeta; prepara una copia de distribución con `python -m qyro_cli bundle --format dir --no-resources`.

Se ejecutaron Tkinter, PySide6, PyQt5, Kivy y las dos integraciones Pydux en Windows/Python 3.13. PyQt6 y PySide2 se revisaron contra el código y sintácticamente; no estaban instalados. El ejemplo PyQt5 emplea un constructor posicional para evitar un fallo observado del wrapper de props.

Para el recorrido completo consulta `../examples.mdx`, `../tooling.mdx` y `../audit-report.mdx`. Los ejemplos evitan usar la carpeta temporal de un build como almacenamiento persistente de usuario.

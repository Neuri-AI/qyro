# 📱 Qyro Kivy Desktop Boilerplate

> **The official, touch-friendly Kivy desktop starter template for the [Qyro](https://github.com/Neuri-AI/qyro) ecosystem.**

[![Python](https://img.shields.io/badge/Python-3.9%20%7C%203.10%20%7C%203.11%20%7C%203.12-blue.svg)](https://python.org)
[![Framework](https://img.shields.io/badge/GUI-Kivy%20(OpenGL)-orange.svg)](https://kivy.org)
[![License](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)

---

## 🌟 Overview

`qyro-boilerplate-kivy` is the official starter template used by `qyro-cli` to scaffold modern, hardware-accelerated desktop and touch applications in seconds. It combines Kivy's flexible, GPU-rendered UI toolkit with Qyro's unified runtime engine.

Ideal for innovative touch interfaces, kiosk software, multimedia tools, and applications requiring custom graphical layouts.

---

## ✨ Features

* **🎨 GPU-Accelerated UI:** Smooth, modern rendering powered by OpenGL.
* **👆 Touch & Gesture Ready:** Native support for multi-touch inputs, drag-and-drop, and gestures.
* **⚡ Reactive State Management:** Centralized state store and event-driven signals directly bound to your app.
* **📦 Smart Resource Resolver:** Automated asset and icon discovery across platforms (`resources/base/`, `resources/windows/`, `resources/mac/`, `resources/linux/`).
* **❄️ Packaging Ready:** Pre-configured for standalone desktop executable bundling with PyInstaller.
* **🔧 Zero-Boilerplate Bootstrap:** Automatic window sizing, title, and icon assignment from `settings/base.json`.

---

## 🚀 Usage

Scaffold a new project automatically using the **Qyro CLI**:

```bash
# Create a Kivy project
qyro init -n my-app --binding Kivy

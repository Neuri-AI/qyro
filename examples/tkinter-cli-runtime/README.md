# 🪶 Qyro Tkinter Desktop Boilerplate

> **The official, zero-dependency Tkinter desktop starter template for the [Qyro](https://github.com/Neuri-AI/qyro) ecosystem.**

[![Python](https://img.shields.io/badge/Python-3.9%20%7C%203.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue.svg)](https://python.org)
[![Framework](https://img.shields.io/badge/GUI-Tkinter%20(Built--in)-green.svg)](https://docs.python.org/3/library/tkinter.html)
[![License](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)

---

## 🌟 Overview

`qyro-boilerplate-tkinter` is the lightweight, zero-dependency starter template used by `qyro-cli` to scaffold desktop applications in seconds. It uses Python's built-in `tkinter` library while giving you modern tooling: reactive state, smart asset resolution, and simplified packaging.

Perfect for lightweight utilities, internal tools, and projects where bundle size and instant startup matter.

---

## ✨ Features

* **🪶 Zero External GUI Dependencies:** Runs out of the box using Python's standard library.
* **⚡ Reactive State Management:** Centralized state store and event subscriptions directly in your Tkinter app.
* **📦 Smart Resource Resolver:** Automated detection of icons and images (`resources/base/`, `resources/windows/`, `resources/mac/`, `resources/linux/`).
* **❄️ Packaging Ready:** Pre-configured for building ultra-compact executables with PyInstaller.
* **🎨 Window Auto-Config:** Automatic window title, sizing, and icon binding from `settings/base.json`.

---

## 🚀 Usage

Scaffold a new project automatically using the **Qyro CLI**:

```bash
# Create a Tkinter project
qyro init -n my-app --binding Tkinter

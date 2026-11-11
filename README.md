# МПСУ: лабораторные и ЛР4 CYBERcobra

Свежая копия репозитория с обновлённым `tb_lab4_demo.sv`: вход `sw` можно менять,
ожидаемый результат и время проверки рассчитываются автоматически.
Остальные лабораторные сохранены. Для ЛР4 начните с инструкции ниже.

## Запуск в Windows с установленной Vivado

В PowerShell:

```powershell
cd "$env:USERPROFILE\Documents"
git clone https://github.com/A2aZel/mpsu-lab4.git mpsu-lab4-new
```

Откройте новую Vivado без проекта. В нижней **Tcl Console** выполните:

```tcl
source [file join $env(USERPROFILE) Documents mpsu-lab4-new Lab4_CYBERcobra walkthrough setup_gui.tcl]
```

Помощник сам создаст проект и добавит исходники. Затем:

1. **Run Simulation → Run Behavioral Simulation**. Дождитесь времени **0 ns**.
2. В Tcl Console:

   ```tcl
   source [file join $env(USERPROFILE) Documents mpsu-lab4-new Lab4_CYBERcobra walkthrough wave_demo.tcl]
   ```

3. **Run All → Zoom Fit**.
4. Для исходного `sw=03B8` ожидаются `test_pass=1`, `out=00000014`,
   `pc=0000002C` и строка `DEMO_PASS`. Завершение — на **850 ns**.

Если Git не установлен, скачайте [ZIP](https://github.com/A2aZel/mpsu-lab4/archive/refs/heads/main.zip)
и распакуйте в Documents. В командах Tcl замените `mpsu-lab4-new` на имя
распакованной папки (обычно `mpsu-lab4-main`).

## Подать другое число

В **Sources → Simulation Sources → tb_lab4_demo** откройте файл и измените:

```systemverilog
logic [15:0] sw = 16'h03b8;
```

Например, замените `03b8` на `0055`. Нажмите **Ctrl+S → Relaunch Simulation →
Run All**. Внутренние проверки менять не нужно. Обычный Restart не перекомпилирует
исходник. Для `0055` результат — `0000000F`; для `FFFF` — `0000FFFF`.
На волнах есть `expected_result`, с которым сравнивается `out`.

Программа собирает биты с чётными номерами (0, 2, 4, …) входного числа подряд.
Вход предварительно знаково расширяется с 16 до 32 бит. Для другого алгоритма
нужно менять программу, а не только `sw`.

## Материалы и проверка

- [Подробный запуск, изменение входа, схема и примеры](Lab4_CYBERcobra/walkthrough/README.md).
- [Устройство процессора и программа варианта 12](Lab4_CYBERcobra/README.md).
- [Исходник демонстрационного тестбенча](Lab4_CYBERcobra/walkthrough/tb_lab4_demo.sv).
- [Остальные лабораторные](HOWTO_RUN.md).

Обновление проверено в Icarus Verilog 13.0: 12 тестов, включая 24 разных входа,
изменение только `sw`, отклонение неправильной программы и продолжение после
успешного завершения. Новая версия тестбенча в Vivado/XSim здесь не запускалась.
Для пересборки под плату используется Nexys A7-100T / `xc7a100tcsg324-1`;
проверка на физической плате остаётся отдельным этапом.

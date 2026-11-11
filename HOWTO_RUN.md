# Как запускать лабы (Vivado) и доп. задание

Для запуска ЛР4 в Windows используйте [инструкцию в README](README.md).
Ниже также сохранены примеры для учебного Linux-сервера и остальных лабораторных.

Плата: **Nexys A7-100T**, FPGA-чип **xc7a100tcsg324-1**.
Скрипты `build_sim.tcl` сами создают проект, добавляют файлы, ставят top-тестбенч
и запускают поведенческую симуляцию. Перед выходом из ПЛИС симуляцию можно гонять
на удалённом сервере; прошивка физической платы — только на ПК, к которому она
подключена.

## 0. Обновить репозиторий на сервере
```bash
cd ~/Desktop/mpsu && git pull
```

## 1. Запуск симуляции (Tcl Console в Vivado)
Всё в одном окне, по очереди. Скрипт сам закрывает предыдущий проект.
Путь подставлен под сервер `/home/pin_31_12/...` — поправь, если другой.
Для **ЛР4** порядок отдельный: свежая Vivado без открытого проекта и переносимый
GUI-помощник; подробности ниже.

```tcl
source /home/pin_31_12/Desktop/mpsu/Lab1_Adder/build_sim.tcl
```
```tcl
source /home/pin_31_12/Desktop/mpsu/Lab2_ALU/build_sim.tcl
```
```tcl
source /home/pin_31_12/Desktop/mpsu/Lab3_Memory/build_sim.tcl
```
```tcl
source {/path/to/mpsu/Lab4_CYBERcobra/walkthrough/setup_gui.tcl}
```
```tcl
source /home/pin_31_12/Desktop/mpsu/Lab5_Decoder/build_sim.tcl
```
```tcl
source /home/pin_31_12/Desktop/mpsu/Lab6_Processor/build_sim.tcl
```
```tcl
source /home/pin_31_12/Desktop/mpsu/Lab7_Peripherals/build_sim.tcl
```
```tcl
source /home/pin_31_12/Desktop/mpsu/Lab8_Programming/build_sim.tcl
```

### ЛР4 — наглядная симуляция для защиты

В команде ЛР4 выше замените путь на свой, сохранив фигурные скобки для пробелов.
Помощник создаёт отдельный проект: hardware top `nexys_CYBERcobra`, simulation top
`tb_lab4_demo`, начальное время **0 ns**. Затем **Run Behavioral Simulation**, в
Tcl Console — `source $wave_script`, **Run For 100 ns → Run All → Zoom Fit**.
Для `SW=03B8` ожидаются `DEMO_PASS`, `checks=43`, `test_pass=1`, `pc=2C`, `out=14`;
35 обычных фронтов после сброса, завершение в 850 ns.

После **Close Simulation** откройте **RTL Analysis → Open Elaborated Design →
dut: CYBERcobra → Schematic**. Пошаговое объяснение — в
[Lab4_CYBERcobra/walkthrough/README.md](Lab4_CYBERcobra/walkthrough/README.md).
В том же TB можно менять `sw`: ожидаемый результат и число шагов определяются
автоматически. После сохранения нажмите **Relaunch Simulation**. Обновление
проверено в Icarus на 24 входах; новая версия в Vivado/XSim здесь не запускалась.

Полный тест ЛР4 запускайте в **отдельном терминале**, из `Lab4_CYBERcobra`:

```bash
vivado -mode batch -nojournal -nolog -source build_sim.tcl -tclargs default exhaustive
```

Для low16 замените `default` на `low16`; ожидается `LAB4_SELF_CHECK=PASS`.
Не выполняйте `source build_sim.tcl` для ЛР4 в GUI: это batch-сценарий для
собственного проекта, который отказывается работать при открытом проекте.
Контракт default32/low16 и границы проверки — в [README ЛР4](Lab4_CYBERcobra/README.md).

## 2. Что считать успехом (по каждой лабе)
| Лаба | Top-тестбенч | Признак успеха |
|------|--------------|----------------|
| Lab1_Adder | `lab_01_tb_fulladder32` | завершился без ошибок |
| Lab2_ALU | `lab_02_tb_alu` | `Number of errors: 0` |
| Lab3_Memory | `lab_03_tb_register_file` | `Number of errors: 0` (и `err_count = 0`) |
| Lab4_CYBERcobra | GUI: `tb_lab4_demo`; полный тест: `tb_lab4_selfcheck` | GUI: `DEMO_PASS`, `test_pass=1` (для `03B8` — 43 проверки); batch: `LAB4_SELF_CHECK=PASS`, `test_pass=1` |
| Lab5_Decoder | `lab_05_tb_decoder` | `Number of errors: 0` |
| Lab6_Processor | `lab_11_tb_processor_system` | `$finish` на строке 45 («The test is over»), НЕ watchdog. У DUT нет выходов — пустая волна (только clk/rst) это норма |
| Lab7_Peripherals | `lab_13_tb_processor_system` | отработал все 4 ms; на волне `led_o` меняется вслед за `sw_i` |
| Lab8_Programming | `lab_13_tb_processor_system` | требует `program.mem` (собранный `init_instr.mem`); без тулчейна процессор простаивает |

### ЛР1 — другие тесты
По умолчанию `fulladder32`. Для остальных:
```tcl
set_property top lab_01_tb_fulladder [get_filesets sim_1]
relaunch_sim
# или lab_01_tb_fulladder4
```

### ЛР6 — показать сигналы на волне (по желанию)
В панели Scope раскрыть `DUT` → в Objects выбрать сигналы (`pc`, `instr_addr_o`,
`instr_i`, `mem_req_o`, `mem_addr_o`) → ПКМ → Add to Wave Window, затем:
```tcl
restart
run all
```

## 3. Прошивка на ПЛИС (на ПК с подключённой платой)
Есть аппаратный top-модуль (board files) у ЛР1–4 и ЛР7.
1. Top = `nexys_adder` / `nexys_alu` / `nexys_rf_riscv` / `nexys_CYBERcobra`
   (для ЛР7 — сам `processor_system`), подключить `nexys_a7_100t.xdc`.
2. `Run Synthesis` → `Run Implementation` → `Generate Bitstream`.
3. Подключить плату по USB, включить питание.
4. `Open Hardware Manager` → `Open Target` → `Auto Connect` →
   `Program Device` → выбрать `.bit` → `Program`.
5. Проверять переключателями/кнопками, смотреть светодиоды/индикаторы.

Лайфхак: `.bit` можно собрать заранее на сервере и в аудитории сделать только шаг 4.

## 4. Доп. задание (RISC-V ассемблер)
Файл `HW_RV32I_asm/hw_variant12.txt` — это НЕ Vivado, запускается в эмуляторе:
- **Venus** (онлайн): https://venus.cs61c.org → Editor (вставить код) →
  Simulator → Assemble & Simulate → Run. Результат: память `0x10010004` и регистр `x10`.
- **Ripes**: File → Open (можно переименовать в `.s`) → Run.

Вариант 12: число из чётных двоичных разрядов входа (`result[k] = input[2*k]`).
Вход/результат в ОЗУ (`0x10010000` / `0x10010004`), результат продублирован в `x10`.
Пример: `input = 0x3B8` → результат `20` (`0x14`).

## 5. Сборка прошивки ЛР8 (если есть RISC-V тулчейн)
В `Lab8_Programming` (git bash, тулчейн `riscv-none-elf-*`):
```bash
CC_DIR=/c/riscv_cc/bin ./build.sh   # путь к bin тулчейна
```
Получить `init_instr.mem`, переименовать в `program.mem`, положить в `Lab8_Programming`,
заменить `memory_pkg.sv` на версию из этой папки (1024/2048) и пересобрать симуляцию.

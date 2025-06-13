# DroidRun Evaluation with AndroidWorld

This module provides tools for benchmarking DroidRun using the [AndroidWorld](https://github.com/google-research/android_world) task suite - a collection of 116 diverse tasks across 20 Android applications.

## Local Setup

### Prerequisites

1. **Python Version Requirements**
   - **Python 3.12** is required
   - Python 3.13 is currently not supported due to compatibility issues with pandas

2. **Android Emulator**
   - Download [Android Studio](https://developer.android.com/studio)
   - Create an Android Virtual Device (AVD):
     - Hardware: **Pixel 6**
     - System Image: **Tiramisu, API Level 33**
     - AVD name: **AndroidWorldAvd**

3. **Prepare AndroidWorld and Droidrun**
   ```bash
   # clone repo
   git clone https://github.com/droidrun/droidrun-android-world && \
   cd droidrun-android-world

   # initialize submodules (android_world + droidrun) + patch android_world setup script
   git submodule update --init && \
   ./scripts/patch-android-wrld.sh ./android_world

   # optionally create a virtual environment beforehand
   pip install .
   ```

4. **Launch the Android Emulator**
   ```bash
   # Typically located in ~/Android/Sdk/emulator/emulator or 
   # ~/Library/Android/sdk/emulator/emulator
   EMULATOR_NAME=AndroidWorldAvd
   ~/Library/Android/sdk/emulator/emulator -avd $EMULATOR_NAME -no-snapshot -grpc 8554
   ```

5. **Install DroidRun Portal App**
   - The DroidRun Portal app must be installed on your Android device or emulator
   - This app provides the accessibility service required for DroidRun to interact with the UI
   - Download and install the APK:
     ```bash
     # Install the portal app using ADB
     adb install -r /path/to/droidrun-portal.apk
     ```
   - The app package name should be `com.droidrun.portal` with service name `com.droidrun.portal.DroidrunPortalService`


6. **Set Environment Variables**
   ```bash
   export OPENAI_API_KEY=your-key  # Or other provider keys
   ```

7. **Important: Initial Emulator Setup**
   
   The first time you run any AndroidWorld benchmark, you **MUST** perform the initial emulator setup to install necessary apps and configure permissions:
   
   ```bash
   # Using our helper script
   ./run_benchmark.sh --task-ids 1 --setup
   
   # Or with the Python module directly
   droidrun-android-world --task-ids 1 --perform-emulator-setup
   ```
   
   This is a one-time setup process that may take several minutes depending on your connection speed. It will install all the necessary apps and configure permissions required by AndroidWorld tasks.

## Docker setup

### Prerequisites

1. **KVM Kernel module**

To run the Android emulator with hardware acceleration in Docker, you must enable KVM (Kernel-based Virtual Machine) on your Linux host.

**Setup steps:**

- **Install KVM and related packages:**
  ```bash
  sudo apt update
  sudo apt install -y qemu-kvm libvirt-daemon-system libvirt-clients bridge-utils
  ```

- **Add your user to the `kvm` and `libvirt` groups:**
  ```bash
  sudo usermod -aG kvm $USER
  sudo usermod -aG libvirt $USER
  # Log out and log back in for group changes to take effect
  ```

- **Verify KVM installation:**
  ```bash
  kvm-ok  # On Ubuntu, from cpu-checker package
  # or
  lsmod | grep kvm
  ```

- **Check that your CPU supports virtualization:**
  ```bash
  egrep -c '(vmx|svm)' /proc/cpuinfo
  # Output should be 1 or more
  ```

- **Ensure `/dev/kvm` exists:**
  ```bash
  ls -l /dev/kvm
  # Should show a character device file
  ```

If you encounter issues, ensure virtualization is enabled in your BIOS/UEFI settings.

For more details, see the [KVM documentation](https://www.linux-kvm.org/page/Main_Page).

2. **Create an alias for easy of use**
```bash
alias droidrun-android-world='docker run --rm -it --name droidrun-android-world \
   --platform linux/amd64 --device /dev/kvm \
   -v ./eval_results:/opt/shared/eval_results \
   -v ./trajectories:/opt/shared/trajectories \
   ${OPENAI_API_KEY:+-e OPENAI_API_KEY} \
   ${GEMINI_API_KEY:+-e GEMINI_API_KEY} \
   ${ANTHROPIC_API_KEY:+-e ANTHROPIC_API_KEY} \
   droidrun/droidrun-android-world:latest "$@"
'
```

## Usage

### Basic Usage

Run a specific task by ID:

```bash
droidrun-android-world --task-ids 1
```

Run a specific task by name:

```bash
droidrun-android-world --task-names ContactsAddContact
```

### List Available Tasks

View all available tasks with their IDs:

```bash
droidrun-android-world --list-tasks
```

### Customizing the Benchmark

```bash
# Run with a different LLM provider and model
droidrun-android-world --task-ids 1 2 3 --llm-provider Anthropic --llm-model claude-3-sonnet-20240229

# Run with initial emulator setup (first time only)
droidrun-android-world --task-ids 1 --perform-emulator-setup

# Set maximum steps per task
droidrun-android-world --task-ids 1 --max-steps 100

# Run multiple parameter combinations per task
droidrun-android-world --task-ids 1 --n-task-combinations 3

# Specify a custom accessibility service name (if different from default)
droidrun-android-world --task-ids 1 --portal-service "com.example.customportal/com.example.customportal.AccessibilityService"
```

### Full Usage Options

```
usage: android_world_bench.py [-h] [--task-ids TASK_IDS [TASK_IDS ...]]
                             [--task-names TASK_NAMES [TASK_NAMES ...]]
                             [--list-tasks]
                             [--n-task-combinations N_TASK_COMBINATIONS]
                             [--llm-provider LLM_PROVIDER]
                             [--llm-model LLM_MODEL] [--temperature TEMPERATURE]
                             [--adb-path ADB_PATH] [--console-port CONSOLE_PORT]
                             [--perform-emulator-setup]
                             [--portal-service PORTAL_SERVICE]
                             [--random-seed RANDOM_SEED]
                             [--results-dir RESULTS_DIR] [--max-steps MAX_STEPS]
                             [--task-family TASK_FAMILY]

Run AndroidWorld benchmark tasks with DroidRun

Task Selection:
  --task-ids TASK_IDS [TASK_IDS ...]
                        Task IDs to run (1-116)
  --task-names TASK_NAMES [TASK_NAMES ...]
                        Task names to run
  --list-tasks         List available tasks and exit
  --n-task-combinations N_TASK_COMBINATIONS
                        Number of parameter combinations per task

LLM Configuration:
  --llm-provider LLM_PROVIDER
                        LLM provider (OpenAI, Anthropic, Gemini, etc.)
  --llm-model LLM_MODEL
                        Model name to use
  --temperature TEMPERATURE
                        Temperature for LLM sampling

Environment Configuration:
  --adb-path ADB_PATH   Path to ADB executable
  --console-port CONSOLE_PORT
                        Emulator console port
  --perform-emulator-setup
                        Perform initial emulator setup (install apps, set permissions)
  --portal-service PORTAL_SERVICE
                        Name of the DroidRun accessibility service

Benchmark Configuration:
  --random-seed RANDOM_SEED
                        Random seed for reproducibility
  --results-dir RESULTS_DIR
                        Directory to save results
  --max-steps MAX_STEPS
                        Maximum steps per task
  --task-family TASK_FAMILY
                        Task family to benchmark
```

## Results

Benchmark results are saved in the specified results directory (default: `eval_results/`). For each task run, the following files are generated:

1. **Individual task result files**: `TIMESTAMP_TASKNAME.json` with detailed information about each task run
2. **Summary file**: `summary.json` with aggregated results across all tasks

After completion, a summary is printed to the console showing:
- Total tasks run
- Success rate
- Average steps per task
- Average execution time

## Accessibility Service Notes

The benchmark script automatically manages the DroidRun accessibility service, which is required for proper interaction with Android UI elements:

1. Before each task, the script will:
   - Disable all existing accessibility services
   - Enable the DroidRun Portal accessibility service
   - Enable accessibility globally
   - Disable any overlay/box rendering if available

2. If you encounter issues with UI interaction:
   - Verify the DroidRun Portal app is installed correctly
   - Check the accessibility service name matches what's in your Portal app
   - Use the `--portal-service` option to provide the correct service name if needed

## Adding to Your Project

This evaluation module is designed as an add-on to the DroidRun framework, not a core dependency. To include it in your project:

1. Copy the `eval` directory to your DroidRun installation
2. Follow the setup instructions above
3. Run the benchmark as described

## Task Categories

AndroidWorld tasks span various applications and interaction types:

- **Contacts**: Add, edit, delete contacts
- **Clock**: Set alarms, use timer, stopwatch
- **Calculator**: Basic and scientific calculations
- **Messages**: Send SMS, share content
- **Settings**: Wi-Fi configuration, display settings
- **Calendar**: Create, edit events
- **Camera**: Take photos, record videos
- **Web Browsing**: Search, navigate websites
- **And more...**

Each task is designed to test agent capabilities across different UI interaction patterns and complexity levels. 
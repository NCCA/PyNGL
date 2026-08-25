#!/usr/bin/env -S uv run --script
"""Run coverage tests without GPU dependencies.
This script separates CPU-only tests from GPU/Qt-dependent tests.
"""

import subprocess
import sys


def run_command(cmd: str, description: str) -> bool:
    """Run a command and return success status."""
    print(f"\n{'=' * 60}")
    print(f"Running: {description}")
    print(f"Command: {cmd}")
    print(f"{'=' * 60}")

    try:
        result = subprocess.run(
            cmd, shell=True, check=True, capture_output=True, text=True
        )
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        return False


def main():
    """Main function to run coverage without GPU."""
    # CPU-only tests (no OpenGL context, no Qt)
    cpu_only_tests = [
        "tests/test_vec2.py",
        "tests/test_vec3.py",
        "tests/test_vec4.py",
        "tests/test_vec2_array.py",
        "tests/test_vec3_array.py",
        "tests/test_vec4_array.py",
        "tests/test_mat2.py",
        "tests/test_mat3.py",
        "tests/test_mat4.py",
        "tests/test_quaternion.py",
        "tests/test_transform.py",
        "tests/test_bbox.py",
        "tests/test_plane.py",
        "tests/test_bezier_curve.py",
        "tests/test_util.py",
        "tests/test_random.py",
        "tests/test_logging.py",
        "tests/test_first_person_camera.py",
        "tests/test_pyside_event_handling_mixin.py",
        "tests/test_image.py",
        "tests/test_webgpu_constants.py",
        "tests/test_webgpu_pipelines.py",
    ]

    # GPU-dependent tests (require OpenGL context)
    gpu_tests = [
        "tests/test_shaderlib.py",
        "tests/test_vao.py",
        "tests/test_texture.py",
        "tests/test_text.py",
        "tests/test_base_mesh.py",
        "tests/test_primitives.py",
        "tests/test_obj.py",
    ]

    # Qt widget tests (require pytest-qt)
    qt_tests = [
        "tests/test_vec2_widget.py",
        "tests/test_vec3_widget.py",
        "tests/test_vec4_widget.py",
        "tests/test_rgb_colour_widget.py",
        "tests/test_rgba_colour_widget.py",
        "tests/test_lookat_widget.py",
        "tests/test_transform_widget.py",
        "tests/test_webgpu_widget.py",
    ]

    print("PyNGL Coverage without GPU")
    print("=" * 60)
    print(f"CPU-only tests: {len(cpu_only_tests)}")
    print(f"GPU tests: {len(gpu_tests)} (skipped)")
    print(f"Qt tests: {len(qt_tests)} (skipped)")

    # Build test file list
    test_files = " ".join(cpu_only_tests)

    # Run coverage
    coverage_cmd = f'uv run coverage run --source=src/ncca/ngl --omit="*/tests/*,*/test_*/__main__.py" -m pytest -p no:pytest-qt {test_files} -v'

    success = run_command(coverage_cmd, "Coverage for CPU-only tests")

    if success:
        # Generate reports
        run_command("uv run coverage report -m", "Coverage report")
        run_command("uv run coverage xml", "Coverage XML for SonarCloud")
        run_command("uv run coverage html", "Coverage HTML report")

        print(f"\n{'=' * 60}")
        print("Coverage completed successfully!")
        print("HTML report available at: htmlcov/index.html")
        print(f"{'=' * 60}")
    else:
        print("\nCoverage failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()

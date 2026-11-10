"""Unit tests of the motor model (no simulator needed): python3 -m pytest src/assem2_robot/tests"""
import math
import os
import sys

import pytest
import rclpy

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
from motor_model import MotorModel  # noqa: E402


@pytest.fixture(scope='module')
def node():
    rclpy.init()
    n = MotorModel()
    n.V_bat = 24.0            # nominal supply, as in the derivation of the report
    yield n
    n.destroy_node()
    rclpy.shutdown()


def test_stall_torque_matches_current_limit(node):
    # tau_max = N eta K_t I_peak = 1 * 1 * 0.64 * 23.4 = 15.0 N.m per wheel
    assert node.tau_available(0.0) == pytest.approx(0.64 * 23.4, rel=1e-3)


def test_no_load_speed_is_voltage_limited(node):
    w0 = 24.0 / 0.64                       # V / (K_e N) = 37.5 rad/s
    assert node.tau_available(w0) == pytest.approx(0.0, abs=1e-6)
    assert node.tau_available(1.2 * w0) == pytest.approx(0.0, abs=1e-6)


def test_torque_falls_with_speed_above_the_current_limit_knee(node):
    w_c = (24.0 - 23.4 * 0.6) / 0.64       # 15.6 rad/s: end of the constant-torque range
    assert node.tau_available(0.9 * w_c) == pytest.approx(14.976, rel=1e-3)
    assert node.tau_available(1.5 * w_c) < node.tau_available(1.1 * w_c) < 14.98


def test_cruise_and_acceleration_torque_match_table(node):
    node.wl = node.wr = 0.6 / 0.08
    tl, tr, F = node.wheel_torques(0.6, 0.0, 0.0, 0.0)
    assert tl == pytest.approx(1.02, abs=0.02) and tr == pytest.approx(tl)
    assert F == pytest.approx(8.4, abs=0.1)
    tl, tr, F = node.wheel_torques(0.6, 1.0, 0.0, 0.0)
    assert tl == pytest.approx(1.58, abs=0.02)
    assert F == pytest.approx(36.7, abs=0.2)


def test_grip_limits_are_far_below_motor_torque(node):
    weight = node.m * node.g
    tau_dry = node.mu_dry * weight * node.r / 4.0
    tau_patch = node.mu_patch * weight * node.r / 4.0
    assert tau_dry == pytest.approx(1.39, abs=0.01)
    assert tau_patch == pytest.approx(0.22, abs=0.01)
    assert node.kt * node.I_peak > 10 * tau_patch      # the wheels spin long before the motor limit


def test_gearbox_ratio_scales_torque_and_current(node):
    t1 = node.tau_available(0.0)
    node.N = 2.0
    try:
        assert node.tau_available(0.0) == pytest.approx(2.0 * t1, rel=1e-3)   # twice the wheel torque at stall
        assert node.tau_available(0.5 * 24.0 / (0.64 * 2.0)) < t1 * 2.0       # back-EMF is reflected through N
    finally:
        node.N = 1.0

import numpy as np
import matplotlib.pyplot as plt
import math
import time
# Work?
mass, w, hbar, kboltz = 1, 1, 1, 1
beta = 10
# beta_array = np.array([1, 2, 3, 6, 8, 10])
beads = 2
# beads_array = np.array([26, 28, 30, 32, 34, 36, 38, 40])
# This evsbeta works
# beads_array = np.array([20, 12, 10, 16, 20, 32])
# Primitive and Virial
# beads_array_p = np.array([10, 20, 30, 40])
# Time
T_max = 2000
dt = 1 * 10 ** (-2)
g_steps = int(T_max / dt)
print("Number of Steps:", g_steps)

# ErrorBars
cutoff = int(g_steps * 0.4)
num_blocks = 40
block_size = int((g_steps-cutoff)/num_blocks)


seed = 347885
np.random.seed(seed)


def initial_position(mass, w, hbar, beads):
    mu, sigma = 0, math.sqrt(hbar / (mass * w))
    x = np.random.normal(mu, sigma, beads)
    return x


def initial_velocity(mass, beta, beads):
    mu, sigma = 0, math.sqrt(1 / (beta * mass))
    vx = np.random.normal(mu, sigma, beads)
    return vx


def oscillator_force(mass, w, beads, x):
    f1 = - mass * w ** 2 * x / beads
    return f1


def ring_springs_force(mass, wp, x):
    c2 = - mass * wp ** 2
    f2 = np.zeros(len(x))
    for j in range(len(x)):
        if j == (len(x) - 1):
            f2[j] = c2 * (2 * x[j] - x[0] - x[j - 1])
        elif j == 0:
            f2[j] = c2 * (2 * x[j] - x[j + 1] - x[-1])
        else:
            f2[j] = c2 * (2 * x[j] - x[j + 1] - x[j - 1])
    return f2


def oscillator_potential(mass, w, x):
    potential = (0.5 * mass * w ** 2 * x ** 2).sum()
    return potential


def springs_potential(mass, wp, x):
    potential = 0
    for j in range(len(x)):
        if j == (len(x) - 1):
            potential += 0.5 * mass * wp ** 2 * (x[0] - x[j]) ** 2
        else:
            potential += 0.5 * mass * wp ** 2 * (x[j + 1] - x[j]) ** 2
    return potential


def kinetic_1d(mass, v):
    kinetic = (0.5 * mass * v ** 2).sum()
    return kinetic


def gamma(dt):  # This is the friction term
    g = 1 / (100 * dt)
    return g


def xsi(beads):  # This is the noise term
    z = np.random.normal(0, 1, beads)
    return z


def langevin(mass, beta, v, dt, beads):
    kin1 = kinetic_1d(mass, v)  # Plus for Ethermo
    c1 = math.exp(-1 * gamma(dt) * dt / 2)
    c2 = math.sqrt((1 / beta / mass) * (1 - c1 ** 2))
    vel = c1 * v + c2 * xsi(beads)
    kin2 = kinetic_1d(mass, vel)  # Minus for Ethermo
    return vel, kin1, kin2


def kinetic_estimator(beta, beads, mass, wp, x):
    k2 = 0
    c2 = 0.5 * mass * wp ** 2
    for j in range(len(x)):
        if j == (len(x) - 1):
            k2 += c2 * (x[j] - x[0]) ** 2
        else:
            k2 += c2 * (x[j] - x[j + 1]) ** 2
    k_estimator = (beads / (2 * beta)) - k2
    return k_estimator


def kinetic_estimator_virial(beads, mass, w, x):
    c2 = 1 / (2*beads)
    k_estimator = (c2 * mass * w**2 * x**2).sum()
    return k_estimator


def langevin_dynamics(g_steps, dt, mass, beta, hbar, kboltz, w, beads):
    wp = math.sqrt(beads) / (beta * hbar)
    x = initial_position(mass, w, hbar, beads)
    vx = initial_velocity(mass, beta, beads)
    force = oscillator_force(mass, w, beads, x) + ring_springs_force(mass, wp, x)
    t = 0
    s = 0
    times = np.zeros(g_steps)
    steps = np.zeros(g_steps)
    kin = np.zeros(g_steps)
    potential = np.zeros(g_steps)
    e_tot = np.zeros(g_steps)
    e_change = np.zeros(g_steps)
    h_eff = np.zeros(g_steps)
    h_eff_change = np.zeros(g_steps)
    temp_exp = np.zeros(g_steps)
    pot_est = np.zeros(g_steps)
    kin_est = np.zeros(g_steps)

    # Histogram
    pos, pos1, pos2, pos3, pos4, pos5, pos6, pos7, pos8 = np.zeros(g_steps), np.zeros(g_steps), np.zeros(g_steps), \
                                                           np.zeros(g_steps), np.zeros(g_steps), np.zeros(g_steps), \
                                                           np.zeros(g_steps), np.zeros(g_steps), np.zeros(g_steps)
    vel = np.zeros(g_steps)
    ethermo = 0.0
    for step in range(0, g_steps):
        times[step] = t
        steps[step] = int(s)
        kin[step] = kinetic_1d(mass, vx)
        potential[step] = oscillator_potential(mass, w, x) / beads + springs_potential(mass, wp, x)
        e_tot[step] = kin[step] + potential[step]
        h_eff[step] = e_tot[step] + ethermo
        h_eff_change[step] = abs((h_eff[step] - h_eff[0]) * 100) / h_eff[0]
        e_change[step] = abs(e_tot[step] - e_tot[0]) * 100 / e_tot[0]
        temp_exp[step] = 2.0 * kin[step] / (kboltz * beads)  # Divided by beads from the Equipartition Function
        pot_est[step] = oscillator_potential(mass, w, x) / beads
        # kin_est[step] = kinetic_estimator(beta, beads, mass, wp, x)
        kin_est[step] = kinetic_estimator_virial(beads, mass, w, x)
        t += dt
        s += 1
        # Histogram
        #Only for 8 Beads
        # pos1[step], pos2[step], pos3[step], pos4[step], pos5[step], pos6[step], pos7[step], pos8[step] = x[0], x[1], x[2], x[3], x[4], x[5], x[6], x[7]
        pos[step] = x[0]
        vel[step] = vx[0]

        # Time propagation
        # vx, kin1, kin2 = langevin(mass, beta, vx, dt, beads)
        # ethermo += kin1 - kin2
        vx = vx + 0.5 * dt * (force / mass)
        x = x + vx * dt
        force = oscillator_force(mass, w, beads, x) + ring_springs_force(mass, wp, x)
        vx = vx + 0.5 * dt * (force / mass)
        # vx, kin1, kin2 = langevin(mass, beta, vx, dt, beads)
        # ethermo += kin1 - kin2
    # pos = (pos1 + pos2 + pos3 + pos4 + pos5 + pos6 + pos7 + pos8) / 8
    return steps, times, pos, vel, kin, potential, e_tot, e_change, temp_exp, pot_est, kin_est, h_eff_change


def block_averaging(cutoff, block_size, data):
    data_cut = data[cutoff:]
    data_len = len(data_cut)
    number_of_blocks = int(data_len/block_size)
    average_array = np.zeros(number_of_blocks)
    for i in range(number_of_blocks):
        average_array[i] = (data_cut[i * block_size:(i + 1) * block_size]).mean()
    averages = average_array.mean()
    stdv = np.std(average_array, ddof=1) / np.sqrt(number_of_blocks)

    return number_of_blocks, averages, stdv




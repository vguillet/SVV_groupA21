from src.class_BOOM import Boom
from math import *
import random
import matplotlib.pyplot as plt
import numpy as np

from config import *


class Slice:
    def __init__(self, label=None, x_location=0):

        self.label = label
        self.x_location = x_location

        self.x_internal_load = 0
        self.y_internal_load = 0
        self.z_internal_load = 0

        self.x_internal_moment = 0
        self.y_internal_moment = 0
        self.z_internal_moment = 0

        self.x_torque = 0
        self.displacement_theta = 0

        # --- Setup boom structure
        self.construct_boom_structure()
        # --- Calculate centroid
        self.calc_centroid()
        # --- Calculate moment of inertia
        self.calc_mom_inertia()
        # --- Calculate shear center
        self.calc_shear_center()

    def construct_boom_structure(self):
        #  ______________________________ Creating boom structure
        booms = []

        r = ha/2
        self.stiffener_pitch = (pi*r + 2*sqrt(r**2+(ca-r)**2))/nst
        self.angle_tail = atan(r/(ca-r))

        stiffener_count = 0

        # --- Adding slanted edge booms
        boom_z = ca-self.stiffener_pitch/2
        while boom_z > r:
            stiffener_count += 2
            boom_y = (ca - boom_z) * tan(self.angle_tail)
            booms.append(Boom(boom_y, boom_z, "Stringer", stiffener_count-1))
            booms.append(Boom(-boom_y, boom_z, "Stringer", stiffener_count))
            boom_z -= self.stiffener_pitch

        # --- Adding sheet booms
        stiffener_count += 2
        booms.append(Boom(r, r, "Spar", stiffener_count-1))
        booms.append(Boom(-r, r, "Spar", stiffener_count))

        # --- Adding circular section booms
        circ_booms = []
        boom_z = 0
        front_stiffeners = nst + 3

        while stiffener_count != nst+1:
            stiffener_count += 2
            front_stiffeners -= 2
            boom_z += self.stiffener_pitch

            circ_booms.append(Boom(-(r * sin(boom_z / r)), r - (r * cos(boom_z / r)), "Stringer", front_stiffeners))
            circ_booms.append(Boom((r * sin(boom_z / r)), r - (r * cos(boom_z / r)), "Stringer", front_stiffeners-1))

        for boom in reversed(circ_booms):
            booms.append(boom)


        # --- Add leading edge boom
        booms.append(Boom(0, 0, "Stringer", nst+2))

        self.booms = booms

        # ______________________________ Creating variables required
        # --- Calculate spar-stringer skin length (trailing edge side)
        self.booms_z_positions = []
        self.booms_y_positions = []

        for boom in booms:
            self.booms_z_positions.append(boom.z_location)
            self.booms_y_positions.append(boom.y_location)

        for i in range(len(booms)):
            if booms[i].type == "Spar":
                spar_label = booms[i].label
                prev_boom_label = booms[i-2].label

                spar_loc = self.booms_z_positions[i]
                prev_boom_loc = self.booms_z_positions[i-2]

        # print("prev_boom_loc", prev_boom_loc, prev_boom_label)
        # print("spar_loc", spar_loc, spar_label)

        self.small_pitch = (prev_boom_loc-spar_loc)/cos(self.angle_tail)
        self.large_pitch = self.stiffener_pitch-self.small_pitch

        # --- List stringers z locations
        self.z_positions_stringers = []
        self.y_positions_stringers = []

        for boom in booms:
            if boom.type == "Stringer":
                self.z_positions_stringers.append(boom.z_location)
                self.y_positions_stringers.append(boom.y_location)
        return

    def calc_centroid(self):

        # ca = 605.0  # [mm]     airfoil cord
        # ha = 205.0  # [mm]     airfoil height
        # tsk = 1.1  # [mm]      skin thickness
        # tst = 1.2  # [mm]      stringer thickness
        # hst = 16.0  # [mm]     height of stringer
        # wst = 19.0  # [mm]     width of stringer

        # List booms z position
        z_pos = []
        for boom in self.booms:
            if boom.type == "Stringer":
                z_pos.append(boom.z_location)
            elif boom.type == "Spar":
                z_spar = boom.z_location

        a_st = wst * tst + (hst - tst) * tst  # area of one stiffener

        # Areas and centroids of parts of cross section from leading edge
        a_circ = np.pi * ha * tsk / 2  # area of circular section
        z_circ = ha / 2 * (1 - 4 / (3 * np.pi))  # centroid of circular section
        a_straight = 2 * tsk * np.sqrt((ca - ha / 2) ** 2 + (ha / 2) ** 2)  # area of both straight parts
        z_straight = ha / 2 + (ca - ha / 2) / 2  # centroid of both straight parts
        a_stiffeners = a_st * len(z_pos)  # area of all stiffeners
        z_stiffeners = sum(z_pos) / len(z_pos)  # centroid of all stiffeners
        a_spar = ha * tsk

        z_centroid = (z_circ * a_circ + z_straight * a_straight + z_stiffeners * a_stiffeners + a_spar * z_spar) / \
                     (a_circ + a_straight + a_stiffeners + a_spar)

        self.u_centroid = z_centroid
        return

    def calc_mom_inertia(self):
        """"Enter lists with the z and y co-ords of the stiffeners and the angle\
        of the skin in the straight section."""

        stif_z = self.z_positions_stringers
        stif_y = self.y_positions_stringers

        angle = self.angle_tail

        ail_h = ha  # height of the aileron     [mm]
        ail_w = ca  # chord of the aileron      [mm]

        # we'll start off by finding moment of inertia for a stiffener
        w = wst  # width of stiffener        [mm]
        h = hst  # height of stiffener       [mm]
        t = tst  # thickness of stiffener    [mm]

        A_base = w * t  # area of the horiz. part   [mm^2]
        A_top = h * t  # area of the vert. part    [mm^2]
        A_stif = A_base + A_top  # area of stiffener         [mm^2]
        self.area_stiffener = A_stif

        c_y = 0  # centroid y co-ord (symm)  [mm]
        c_z = self.u_centroid  # centroid z co-ord         [mm]
        # c_z = ail_h / 2

        stif_zz = 0  # initial value mom inert   [mm^4]
        stif_yy = 0  # initial value mom inert   [mm^4]

        for i in range(len(stif_y)):
            if stif_y[i] < 0:
                stif_y[i] = stif_y[i] + 3
            elif stif_y[i] > 0:
                stif_y[i] = stif_y[i] - 3

        for i in range(len(stif_z)):
            stif_z[i] = stif_z[i] - c_z

        # now calculate the Steiner terms for all stiffeners
        for i in range(len(stif_z)):
            stein_z = A_stif * (stif_z[i]) ** 2
            stif_yy = stif_yy + stein_z

        for i in range(len(stif_y)):
            stein_y = A_stif * (stif_y[i]) ** 2
            stif_zz = stif_zz + stein_y

        skin_t = 1.1  # skin thickness        [mm]
        skin_l = np.sqrt((ail_w - (ail_h / 2)) ** 2 + (ail_h / 2) ** 2)  # skin length           [mm]

        # add the moment of inertia for the straight part of the skin
        skin_zz1 = ((skin_t * (skin_l / 2) ** 3) * np.sin(angle) ** 2) / 12
        skin_yy1 = ((skin_t * (skin_l / 2) ** 3) * np.cos(angle) ** 2) / 12
        skin_stein_1a = skin_t * skin_l * (np.cos(angle) * skin_l / 2) ** 2
        skin_stein_1b = skin_t * skin_l * (np.sin(angle) * skin_l / 2) ** 2

        skin_zz2 = ((skin_t * (skin_l / 2) ** 3) * np.sin(angle) ** 2) / 12
        skin_yy2 = ((skin_t * (skin_l / 2) ** 3) * np.cos(angle) ** 2) / 12
        skin_stein_2a = skin_t * skin_l * (np.cos(angle) * skin_l / 2) ** 2
        skin_stein_2b = skin_t * skin_l * (-np.sin(angle) * skin_l / 2) ** 2

        skin_zz = skin_zz1 + skin_zz2 + skin_stein_1b + skin_stein_2b
        skin_yy = skin_yy1 + skin_yy2 + skin_stein_1a + skin_stein_2a

        z_out = (ail_h / 2) - (4 * ail_h / 2) / (3 * np.pi)  # centroid outer        [mm]
        z_in = (ail_h / 2) - (4 * (ail_h - skin_t) / 2) / (3 * np.pi)  # centroid inner        [mm]
        A_out = (np.pi * (ail_h / 2) ** 2) / 2  # area outer circ       [mm^2]
        A_in = (np.pi * ((ail_h - skin_t) / 2) ** 2) / 2  # area inner circ       [mm^2]
        circ_z = (A_out * z_out + A_in * z_in) / (A_out + A_in)  # centroid z            [mm]

        # add the moment of inertia for the circular part of the skin
        circ_zz = A_out * (ail_h / 2) ** 2 / 4 - A_in * ((ail_h - skin_t) / 2) ** 2 / 4
        circ_yy = A_out * (ail_h / 2) ** 2 / 4 - A_in * ((ail_h - skin_t) / 2) ** 2 / 4
        circ_stein = (A_in + A_out) * (circ_z - c_z) ** 2

        spar_z = ail_h / 2  # centroid of the spar      [mm]
        spar_h = ail_h  # height of the spar        [mm]
        spar_t = 2.8  # thickness of spar         [mm]

        # finally, add the moment of inertia for the spar
        spar_zz = (spar_h * spar_t ** 3) / 12
        spar_yy = (spar_t * spar_h ** 3) / 12
        spar_stein = spar_h * spar_t * (spar_z - c_z) ** 2

        # then add all the moment of inertia together
        I_u = stif_zz + skin_zz + circ_zz + spar_zz
        I_v = stif_yy + skin_yy + circ_yy + circ_stein + spar_yy + spar_stein

        # now switch to the new axis system
        phi = np.radians(28)  # aileron rot angle         [rad]
        I_zz = (I_u + I_v) / 2 + ((I_u - I_v) / 2) * np.cos(2 * phi)
        I_yy = (I_u + I_v) / 2 - ((I_u - I_v) / 2) * np.cos(2 * phi)
        J = I_yy + I_zz

        self.I_u = I_u
        self.I_v = I_v

        self.I_zz = I_zz
        self.I_yy = I_yy

        self.polar_I_uv = self.I_u + self.I_v
        self.polar_I_zy = self.I_zz + self.I_yy
        return

    def calc_shear_center(self):

        # S_y/I_xz
        I_xx = 1565571000
        # I_xx = self.I_u  # mm^4

        spar_height = ha
        t_1 = tsk
        t_2 = tsp

        angle = degrees(self.angle_tail)
        # print (angle)

        z_pos = self.booms_z_positions
        y_pos = self.booms_y_positions
        # print(z_pos)
        # print(y_pos)

        boomarea = []
        boomarea2 = []

        # --- boom area 1 and 2
        b1 = (t_1 * self.stiffener_pitch) / 6 * (2 + y_pos[1] / y_pos[0]) + self.area_stiffener + (t_1 * self.stiffener_pitch) / 6 * (
                    2 + y_pos[2] / y_pos[0])
        boomarea2.append(b1)
        boomarea2.append(b1)

        # --- boom area 3 to 10
        for i in range(0, 4):
            j = 2 + 2 * i
            b2 = ((t_1 * self.stiffener_pitch) / 6) * (2 + y_pos[j - 2] / y_pos[j]) + self.area_stiffener + ((t_1 * self.stiffener_pitch) / 6) * (
                        2 + y_pos[j + 2] / y_pos[j])
            boomarea2.append(b2)
            boomarea2.append(b2)
            # boom area 11 and 12
        b11 = (t_1 * self.small_pitch) / 6 * (2 + y_pos[12] / y_pos[10]) + self.area_stiffener + (t_1 * self.stiffener_pitch) / 6 * (
                    2 + y_pos[8] / y_pos[10])
        boomarea2.append(b11)
        boomarea2.append(b11)

        # --- boom area 13 and 14
        b13 = (t_2 * spar_height) / 6 * (2 + y_pos[13] / y_pos[12]) + (t_1 * self.small_pitch) / 6 * (2 + y_pos[10] / y_pos[12]) + (
                    t_1 * self.large_pitch) / 6 * (2 + y_pos[14] / y_pos[12])
        boomarea2.append(b13)
        boomarea2.append(b13)

        # --- boom area 15 and 16
        b15 = (t_1 * self.large_pitch) / 6 * (2 + y_pos[12] / y_pos[14]) + self.area_stiffener + (t_1 * self.stiffener_pitch) / 6 * (
                    2 + y_pos[16] / y_pos[14])
        boomarea2.append(b15)
        boomarea2.append(b15)

        # --- boom area 17
        b17 = ((t_1 * self.stiffener_pitch) / 6) * 2 + self.area_stiffener
        boomarea2.append(b17)
        boomarea = boomarea2
        q_bottom = [0]
        q_prev = float(0)
        for i in range(0, 6):
            j = 11 - (2 * i)
            q = (-boomarea[j] / I_xx) * y_pos[j] + q_prev
            q_prev = q
            q_bottom.append(q)
        # print(q_bottom)
        # print (q_bottom[-1])

        q_top = []
        q_prev = q_bottom[-1]
        for i in range(0, 5):
            j = (2 * i)
            q = (-boomarea[j] / I_xx) * y_pos[j] + q_prev
            q_prev = q
            q_top.append(q)
        q_top.append(0)
        # print(q_top)

        q_spar = []
        q = (-boomarea[13] / I_xx) * y_pos[13]
        q_spar.append(q)
        # print(q_spar)

        q_curve = [0]

        q16 = (-boomarea[15] / I_xx) * y_pos[15]
        q_curve.append(q16)
        q17 = (-boomarea[16] / I_xx) * y_pos[16] + q16
        q_curve.append(q17)
        # q15=(-boomarea[14]/I_xx)*boomy[14]+q17
        # q_curve.append(q15)
        q_curve.append(0)
        # print(q_curve)

        q_right = q_bottom + q_top

        a_1 = ((q_curve[1] + q_curve[2]) * self.stiffener_pitch) / t_1
        b_1 = -(q_spar[0]) * spar_height / t_2

        m_1 = ((2 * self.stiffener_pitch + 2 * self.large_pitch) / t_1) + (spar_height / t_2)
        m_2 = (-spar_height / t_2)

        a_2 = (sum(q_right) * self.stiffener_pitch) / t_1
        b_2 = (q_spar[0]) * spar_height / t_2

        n_1 = (-spar_height / t_2)
        n_2 = ((11 * self.stiffener_pitch + 2 * self.small_pitch) / t_1) + (spar_height / t_2)
        # print(m_1,m_2,a_1,b_1,n_1,n_2,a_2,b_2)
        A = np.array([[m_1, m_2], [n_1, n_2]])
        B = np.array([[-a_1 - b_1], [-a_2 - b_2]])
        # print (np.linalg.solve(A, B ))
        q_s0 = np.linalg.solve(A, B)
        q_s01 = q_s0[0][0]
        q_s02 = q_s0[1][0]
        d = spar_height * sin(radians(90 - angle))

        # --- M around 5 by upper part
        M_1 = (((-q_s02 * 5 + sum(q_top[0:5])) * self.stiffener_pitch) + (-q_s02 * self.small_pitch)) * d

        # --- M caused by q between 1 and 2
        M_2 = (q_bottom[-1] - q_s02) * (y_pos[0] - y_pos[1]) * (z_pos[0] - z_pos[14])

        # M --- caused by curve
        M_3 = -((q_curve[1] + q_s01) * (2 * (y_pos[14])) * (z_pos[13] - z_pos[14]))
        M_4 = -((q_s01 * (z_pos[13] - z_pos[14]) * (y_pos[14] - y_pos[13])) + (q_s01 * (y_pos[12] - y_pos[14]) * (z_pos[13] - z_pos[14])))

        M = M_1 + M_2 + M_3 + M_4
        shearcenter_u = M + (spar_height / 2)

        self.shear_center_u = shearcenter_u

    def plot_boom_structure(self):
        label_stringer = []

        z_spar = []
        y_spar = []
        label_spar = []

        for i in range(len(self.booms)):
            if self.booms[i].type == "Stringer":
                label_stringer.append(self.booms[i].label)
            elif self.booms[i].type == "Spar":
                z_spar.append(self.booms[i].z_location)
                y_spar.append(self.booms[i].y_location)
                label_spar.append(self.booms[i].label)

        plt.scatter(self.z_positions_stringers, self.y_positions_stringers, color='b', label="Stringers")
        plt.scatter(z_spar, y_spar, color='r', label="Spar")

        for i, txt in enumerate(label_stringer):
            plt.annotate(txt, (self.z_positions_stringers[i], self.y_positions_stringers[i]))

        for i, txt in enumerate(label_spar):
            plt.annotate(txt, (z_spar[i], y_spar[i]))

        i = 1
        upper_half_z = [ca]
        upper_half_y = [0]

        lower_half_z = [ca]
        lower_half_y = [0]

        while i < len(self.booms_z_positions):
            upper_half_y.append(self.booms_y_positions[i-1])
            upper_half_z.append(self.booms_z_positions[i-1])

            lower_half_y.append(self.booms_y_positions[i])
            lower_half_z.append(self.booms_z_positions[i])

            i += 2

        upper_half_y.append(0)
        upper_half_z.append(0)

        lower_half_y.append(0)
        lower_half_z.append(0)

        plt.plot(upper_half_z, upper_half_y, color="g")
        plt.plot(lower_half_z, lower_half_y, color="g")

        plt.title("Cross-section boom structure of the aileron")
        plt.xlabel("x (mm)")
        plt.ylabel("y (mm)")

        plt.legend()
        plt.grid()
        plt.axis("equal")
        plt.show()


class Simple_slice(Slice):
    def __init__(self, label, x_location):
        Slice.__init__(self, label, x_location)

        self.x_load = 0
        self.y_load = 0
        self.z_load = 0

    def __repr__(self):
        return "Simple slice " + str(self.label)


class Hinged_slice(Slice):
    def __init__(self, label, x_location, x_load=0, y_load=0, z_load=0):
        Slice.__init__(self, label, x_location)

        self.x_load = x_load
        self.y_load = y_load
        self.z_load = z_load

    def __repr__(self):
        return "Hinged slice " + str(self.label)


class Rib(Slice):
    def __init__(self, label, x_location, deflection=0, x_load=0, y_load=0, z_load=0):
        Slice.__init__(self, label, x_location)

        self.deflection = deflection

        self.x_load = x_load
        self.y_load = y_load
        self.z_load = z_load

    def calc_shear_flow(self):

        # S_y/I_xzz
        # I_xx=161250000 #mm^4
        # self.large_pitch = 81.33511390749766
        # small_pitch = 8.512094985784858
        # Tx = 10000

        CGz = self.u_centroid
        spar_height = ha

        C_a = ca  # mm
        t_1 = tsk
        t_2 = tsp
        angle = degrees(self.angle_tail)

        SCu = self.shear_center_u  # mm
        Tx = self.x_torque

        # Sy = 123
        # Sz = 234
        # Mz = 120
        # My = 100
        Sz = self.z_internal_load * cos(radians(theta)) + self.y_internal_load * sin(radians(theta))
        Sy = self.y_internal_load * cos(radians(theta)) - self.z_internal_load * sin(radians(theta))

        Mz = self.z_internal_moment * cos(radians(theta)) + self.y_internal_moment * sin(radians(theta))
        My = self.y_internal_moment * cos(radians(theta)) - self.z_internal_moment * sin(radians(theta))

        # print (angle)
        z_pos = self.booms_z_positions
        # print(z_pos)
        y_pos = self.booms_y_positions
        # print(y_pos)

        # =========================================
        Nstress = []

        for i in range(0, 17):
            stress = Mz / self.I_u * y_pos[i] + My / self.I_v * (z_pos[i] - CGz)
            Nstress.append(stress)

        boomarea = []
        b1 = (t_1 * self.stiffener_pitch) / 6.0 * (2 + Nstress[1] / Nstress[0]) + (t_1 * self.stiffener_pitch) / 6.0 * \
             (2 + Nstress[2] / Nstress[0]) + self.area_stiffener
        boomarea.append(b1)
        b2 = (t_1 * self.stiffener_pitch) / 6.0 * (2 + Nstress[0] / Nstress[1]) + (t_1 * self.stiffener_pitch) / 6.0 * \
             (2 + Nstress[3] / Nstress[1]) + self.area_stiffener
        boomarea.append(b2)
        for i in range(0, 8):
            j = 2 + i
            b = (t_1 * self.stiffener_pitch) / 6.0 * (2.0 + Nstress[j - 2] / Nstress[j]) + (t_1 * self.stiffener_pitch) / 6.0 * (
                    2.0 + Nstress[j + 2] / Nstress[j]) + self.area_stiffener

            # print(j)
            # print(Nstress[j] / Nstress[j - 2])
            boomarea.append(b)

        for i in range(0, 2):
            j = 10 + i
            b = (t_1 * self.stiffener_pitch) / 6.0 * (2.0 + Nstress[j - 2] / Nstress[j]) + (t_1 * self.small_pitch) / 6.0 * (
                    2.0 + Nstress[j + 2] / Nstress[j]) + self.area_stiffener
            boomarea.append(b)

        b13 = (t_1 * self.small_pitch) / 6.0 * (2.0 + Nstress[10] / Nstress[12]) + (t_1 * self.large_pitch) / 6.0 * (
                2.0 + Nstress[14] / Nstress[12]) + (t_2 * spar_height) / 6.0 * (2.0 + Nstress[13] / Nstress[12])
        boomarea.append(b13)
        b14 = (t_1 * self.small_pitch) / 6.0 * (2.0 + Nstress[11] / Nstress[13]) + (t_1 * self.large_pitch) / 6.0 * (
                2.0 + Nstress[15] / Nstress[13]) + (t_2 * spar_height) / 6.0 * (2.0 + Nstress[12] / Nstress[13])
        boomarea.append(b14)
        b15 = (t_1 * self.large_pitch) / 6.0 * (2.0 + Nstress[12] / Nstress[14]) + (t_1 * self.stiffener_pitch) / 6.0 * (
                2.0 + Nstress[16] / Nstress[14]) + self.area_stiffener
        boomarea.append(b15)
        b16 = (t_1 * self.large_pitch) / 6.0 * (2.0 + Nstress[13] / Nstress[15]) + (t_1 * self.stiffener_pitch) / 6.0 * (
                2.0 + Nstress[16] / Nstress[15]) + self.area_stiffener
        boomarea.append(b16)
        b17 = (t_1 * self.stiffener_pitch) / 6.0 * (2.0 + Nstress[15] / Nstress[16]) + (t_1 * self.stiffener_pitch) / 6.0 * (
                2.0 + Nstress[14] / Nstress[16]) + self.area_stiffener
        boomarea.append(b17)

        # =============================================

        q_bottom = [0]
        q_prev = float(0)
        for i in range(0, 6):
            j = 11 - (2 * i)
            q = (-boomarea[j] * Sy / self.I_u) * y_pos[j] - (boomarea[j] * Sz / self.I_v) * (z_pos[j] - CGz) + q_prev
            q_prev = q
            q_bottom.append(q)
        # print(q_bottom)
        # print(q_bottom[-1])

        q_top = []
        q_prev = q_bottom[-1]
        for i in range(0, 6):
            j = (2 * i)
            q = (-boomarea[j] * Sy / self.I_u) * y_pos[j] - (boomarea[j] * Sz / self.I_v) * (z_pos[j] - CGz) + q_prev
            q_prev = q
            q_top.append(q)
        # print(q_top)

        q_spar = []
        q = (-boomarea[13] * Sy / self.I_u) * y_pos[13] - (boomarea[13] * Sz / self.I_v) * (z_pos[13] - CGz)
        q_spar.append(q)
        # print(q_spar)

        q_curve = [0]
        q16 = (-boomarea[15] * Sy / self.I_u) * y_pos[15] - (boomarea[15] * Sz / self.I_v) * (z_pos[15] - CGz)
        q_curve.append(q16)
        q17 = (-boomarea[16] * Sy / self.I_u) * y_pos[16] - (boomarea[16] * Sz / self.I_v) * (z_pos[16] - CGz) + q16
        q_curve.append(q17)
        q15 = (-boomarea[14] * Sy / self.I_u) * y_pos[14] - (boomarea[14] * Sz / self.I_v) * (z_pos[14] - CGz) + q17
        q_curve.append(q15)
        # print(q_curve)

        d = spar_height * sin(radians(90 - angle))
        A1 = 1.0 / 4.0 * pi * spar_height * spar_height * 0.5
        A2 = 0.5 * spar_height * (C_a - 0.5 * spar_height)
        # Moment around boom 14 by top CCW positive
        M1 = sum(q_top[0:5]) * d * self.stiffener_pitch + q_top[5] * self.small_pitch * d
        # Moment by q12
        M2 = q_bottom[-1] * (y_pos[0] - y_pos[1]) * (z_pos[0] - z_pos[14])
        # Moment by curved part
        M3 = -q_curve[1] * (y_pos[16] - y_pos[15]) * (z_pos[13] - z_pos[15]) + q_curve[1] * (z_pos[15] - z_pos[16]) * (
                y_pos[15] - y_pos[13])
        M4 = -q_curve[2] * (y_pos[14] - y_pos[16]) * (z_pos[13] - z_pos[16]) - q_curve[2] * (z_pos[14] - z_pos[16]) * (
                y_pos[16] - y_pos[13])
        M5 = -q_curve[3] * (y_pos[12] - y_pos[14]) * (z_pos[13] - z_pos[14]) - q_curve[3] * (z_pos[12] - z_pos[14]) * (
                y_pos[14] - y_pos[13])
        # Moments due to q_s0
        M6 = -2.0 * A1  # times q_s01
        M7 = -2.0 * A2  # times q_s02

        #
        #
        #
        #
        # Moments by external forces
        # M = -Rz*0.5*spar_height - P*cos(radians(theta))*spar_height + P*sin(radians(theta))*(z_pos[13]-z_pos[16])
        M = -Sz * 0.5 * spar_height + Sy * (SCu - z_pos[13]) - Tx

        # Compute the angle of twist for curved cell (clockwise positive)
        k1 = sum(q_curve[1:3]) * self.stiffener_pitch / t_1 + q_curve[3] * self.large_pitch / t_1 - q_spar[0] * spar_height / t_2
        l1 = 2.0 * (self.stiffener_pitch + self.large_pitch) / t_1 + spar_height / t_2  # times qs01
        m1 = -spar_height / t_2  # times qs02

        # Compute the angle of twist for triangular cell (clockwise positive)
        k2 = -sum(q_bottom) * self.stiffener_pitch / t_1 + -sum(q_top[0:5]) * self.stiffener_pitch / t_1 + -q_top[
            5] * self.small_pitch / t_1 + q_spar[
                 0] * spar_height / t_2
        l2 = -spar_height / t_2  # times qs01
        m2 = (2.0 * self.small_pitch + 11.0 * self.stiffener_pitch) / t_1 + spar_height / t_2

        A = np.array([[M6, M7], [(l1 - l2), (m1 - m2)]])
        B = np.array([[(M - (M1 + M2 + M3 + M4 + M5))], [(k2 - k1)]])
        # print(np.linalg.solve(A, B))
        q_s0 = np.linalg.solve(A, B)
        q_s01 = q_s0[0][0]
        q_s02 = q_s0[1][0]

        # Since the axial force in the skin is horizontal slightly left of the spar the shear flow in
        # the rib is just to compensate for the vertical components of the shearflows
        q1 = ((q_s01 * (y_pos[15] - y_pos[13])) + ((q_curve[1] + q_s01) * (y_pos[16] - y_pos[15])) + (
                (q_curve[2] + q_s01) * (y_pos[14] - y_pos[16])) + ((q_curve[3] + q_s01) * (y_pos[12] - y_pos[14]))) / spar_height

        q11 = (q_s01 * spar_height + ((q_curve[1]) * (y_pos[16] - y_pos[15])) + ((q_curve[2]) * (y_pos[14] - y_pos[16])) + (
                (q_curve[3]) * (y_pos[12] - y_pos[14]))) / spar_height

        # Calculate q2 the shear flow in the rib slightly right of the spar
        P13z = ((2.0 * q_s02 * A2) + ((sum(q_top[0:5]) * self.stiffener_pitch + self.small_pitch * q_top[-1]) * d) + (
                q_bottom[-1] * self.stiffener_pitch / 2.0 * d)) / spar_height
        P13y = P13z * tan(radians(angle))

        q2 = ((-q_s02 * spar_height) + sum(q_bottom) * (y_pos[9] - y_pos[11]) + sum(q_top[0:5]) * (y_pos[4] - y_pos[2]) + q_top[-1] * (
                y_pos[12] - y_pos[10]) - P13y) / spar_height

        self.q1 = q1
        self.q2 = q2
    def __repr__(self):
        return "Rib " + str(self.label)

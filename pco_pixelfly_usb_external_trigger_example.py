import numpy as np
from tifffile import imread, imwrite
import pco_pixelfly_usb
import ni_PCIe_6738

'''Test the camera's ability to follow external triggers'''
ao = ni_PCIe_6738.DAQ(num_channels=1, rate=1e6, verbose=False)

camera = pco_pixelfly_usb.Camera(verbose=True)
frames = 10
camera.apply_settings(frames, 1, 'min', 'binary+ASCII')

jitter_time_us = 2000 # how much slop is needed between triggers? 2000us?
jitter_px = max(ao.s2p(1e-6 * jitter_time_us), 1)
read_px = ao.s2p(1e-6 * camera.read_time_us)
exposure_px = ao.s2p(1e-6 * camera.exposure_us)
period_px = read_px + exposure_px + jitter_px

voltage_series = []
for i in range(frames):
    volt_period = np.zeros((period_px, ao.num_channels), 'float64')
    volt_period[:read_px, 0] = 5 # (falling edge is time for laser on!)
    voltage_series.append(volt_period)
voltages = np.concatenate(voltage_series, axis=0)

# can the camera keep up?
ao._write_voltages(voltages) # write voltages first to avoid delay
images = np.zeros( # allocate memory to pass in
    (camera.num_images, camera.height_px, camera.width_px),'uint16')

for i in range(2):
    ao.play_voltages(block=False) # race condition!
    camera.record_to_memory( # -> waits for trigger
        allocated_memory=images, software_trigger=False, re_arm=True)
imwrite('test_external_trigger.tif', images, imagej=True)

time_s = ao.p2s(voltages.shape[0])
fps = frames /  time_s
print('fps = %02f'%fps) # (forced by ao play)

camera.close()
ao.close()

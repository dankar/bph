import pyaudio
import struct
import math

seconds_to_measure = 4
target_hz = 5.5
tolerance = 0.3

pa = pyaudio.PyAudio()

device_index = None            
for i in range(pa.get_device_count()):     
    devinfo = pa.get_device_info_by_index(i)   

    for keyword in ["mic","input"]:
        if keyword in devinfo["name"].lower():
            device_index = i
            break
            
    if device_index != None:
        break
        
sample_rate = 44100   
samples_per_block = sample_rate*seconds_to_measure
stream = pa.open(format = pyaudio.paInt16, channels = 1, rate = sample_rate, input = True, input_device_index = device_index, frames_per_buffer = samples_per_block)

sens_val = 0.5
skip_val = target_hz * 20.0
skip_counter = 0
ticks_per_measure = target_hz * seconds_to_measure
adjustment = 0.9

while True:
    block = stream.read(samples_per_block)
    count = len(block)/2
    shorts = struct.unpack("%dh"%(count), block)
    total_ticks = 0
    count = 0
    
    ticks = []
    
    for sample in shorts:
        fsample = sample / 32768.0
        count = count + 1
        if skip_counter > 0:
            skip_counter = skip_counter - 1
            #print skip_counter
        elif math.fabs(fsample) > sens_val:
            ticks.append(count)
            total_ticks = total_ticks + 1
            skip_counter = samples_per_block / skip_val
            
    print "Adjusting sensitivity by", adjustment
    if total_ticks < ticks_per_measure:
        sens_val = sens_val * (1.0 - adjustment)
    if total_ticks > ticks_per_measure:
        adjustment = adjustment * 0.7
        sens_val = sens_val / (1.0 - adjustment)
        
    diffs = []
    
    if total_ticks > 0:
        previous_tick = ticks[0]
        for tick in ticks:
            diff = tick - previous_tick
            previous_tick = tick
            
            if diff > 0:
                
                # Account for missing beats by dividing the diff by 2
                while diff > (sample_rate / target_hz) * 1.5: 
                    diff = diff / 2.0
                    
                # If it still doesn't fit into the pattern, don't append it
                if diff > (sample_rate / target_hz) * (1.0 - tolerance) and diff < (sample_rate / target_hz) * (1.0 + tolerance):
                    diffs.append(diff)
                    
        print "Got roughly", total_ticks / seconds_to_measure, "ticks per seconds"
        print "", len(diffs), "usable diffs (should be around", target_hz * seconds_to_measure, "for reliable calculations)"
        if len(diffs) > (target_hz * 0.8): 
            x = float(sum(diffs)) / float(len(diffs))
            hz = sample_rate / x
            print "Average:", hz, "hz"
            print "Error:", hz - target_hz, "hz"
        else:
            print "Not enough measurements to calculate hz"
    
    
    


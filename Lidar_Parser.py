import serial

port_name = "COM3"
baudrate = 230400

ser = serial.Serial(port = port_name, baudrate = baudrate , bytesize = 8, timeout = 1)
# stop bit set to one by default
buffer = bytearray()
packet = bytearray()


def decode_metrics(packet_arr):
    metrics  = []
    speed_deg_s = packet_arr[2]+(packet_arr[3] * 256)
    start_angle_deg = (packet_arr[4] + packet_arr[5] * 256)/100
    metrics.append(speed_deg_s)
    metrics.append(start_angle_deg)
    end_angle_deg = (packet_arr[42] + packet_arr[43] *256)/100

    count = 0
    for x in range(6,42,3):
        count+=1
        point_distance = (packet_arr[x]+packet_arr[x+1]*256)
        point_intensity = packet_arr[x+2]
        point_angle = start_angle_deg+((end_angle_deg - start_angle_deg)/11 * count)
        metrics.append(point_distance)
        metrics.append(point_intensity)
        metrics.append(point_angle)

    
    metrics.append(end_angle_deg)





    return metrics



def check_crc(packet_arr):
    crc = 0
    for x in packet_arr[0:46]:
        crc = crc ^ x
        for r in range(0,8,1):
            if crc & 0x80:
                crc = (crc << 1) ^ 0x4D

            else:
                crc = crc << 1

            crc = crc & 0xFF

    if crc == packet_arr[46]:
        return True

    else: 
        return False


            



    













while True:
    while ser.in_waiting>0:
        buffer+=ser.read(ser.in_waiting)
        starting_index = buffer.find(b"\x54\x2c")

        if starting_index != -1:

            packet = buffer[starting_index:starting_index+47]


            if len(packet) == 47:
                if check_crc(packet):
                    metrics = decode_metrics(packet)
                    print(metrics)
                    packet.clear()
                    del buffer[0:starting_index+47]

                else:

                    del buffer[0:starting_index+1]









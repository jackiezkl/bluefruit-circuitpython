import time, displayio, terminalio, adafruit_imageload
from adafruit_debouncer import Debouncer
from adafruit_gizmo import tft_gizmo
from adafruit_display_text import label
from adafruit_ble import BLERadio
from adafruit_ble.advertising.standard import ProvideServicesAdvertisement
from adafruit_ble.services.nordic import UARTService
from adafruit_circuitplayground import cp

# --| User Config |---------------------------------------------------
#enter your name and your friend's name below:
my_name = "Charlie"
friend_name = "Delta"
#anwer who will be the host
host = "Delta"
# --| User Config |---------------------------------------------------


BLE_MODE = my_name

if BLE_MODE not in (my_name, friend_name):
    raise ValueError("Enter the names in line 12  and 13.")

# Define Morse Code dictionary
morse_code = {
    ".-": "A",
    "-...": "B",
    "-.-.": "C",
    "-..": "D",
    ".": "E",
    "..-.": "F",
    "--.": "G",
    "....": "H",
    "..": "I",
    ".---": "J",
    "-.-": "K",
    ".-..": "L",
    "--": "M",
    "-.": "N",
    "---": "O",
    ".--.": "P",
    "--.-": "Q",
    ".-.": "R",
    "...": "S",
    "-": "T",
    "..-": "U",
    "...-": "V",
    ".--": "W",
    "-..-": "X",
    "-.--": "Y",
    "--..": "Z",
}

WAIT_FOR_DOUBLE = 0.05

display = tft_gizmo.TFT_Gizmo()
button_a = Debouncer(lambda: cp.button_a == 0)
button_b = Debouncer(lambda: cp.button_b == 0)

# BLE Radio Stuff
if BLE_MODE == host:
    MY_NAME = "Me"
    FRIENDS_NAME = "Friend"
else:
    MY_NAME = "Friend"
    FRIENDS_NAME = "Me"
ble = BLERadio()
uart_service = UARTService()
advertisement = ProvideServicesAdvertisement(uart_service)
ble._adapter.name = MY_NAME  # pylint: disable=protected-access

disp_group = displayio.Group()
display.root_group = disp_group

# Background BMP with the Morse Code cheat sheet
bmp, pal = adafruit_imageload.load(
    "images/morse_bg.bmp", bitmap=displayio.Bitmap, palette=displayio.Palette
)
disp_group.append(displayio.TileGrid(bmp, pixel_shader=pal))

# Incoming messages show up here
in_label = label.Label(terminalio.FONT, text="A" * 18, scale=2, color=0x000000)
in_label.anchor_point = (1.0, 0)
in_label.anchored_position = (235, 4)
disp_group.append(in_label)

# Outging messages show up here
out_label = label.Label(terminalio.FONT, text="B" * 18, scale=2, color=0x000000)
out_label.anchor_point = (1.0, 0)
out_label.anchored_position = (235, 180)
disp_group.append(out_label)

# Morse Code entry happens here
edit_label = label.Label(terminalio.FONT, text="----", scale=2, color=0x000000)
edit_label.anchor_point = (0.5, 0)
edit_label.anchored_position = (115, 212)
disp_group.append(edit_label)


def scan_and_connect():
    """
    Handles initial connection between the two CLUES.
    Return is a UART object that can be used for read/write.
    """

    print("Connecting...")
    in_label.text = out_label.text = "Connecting..."

    if MY_NAME == "Me":
        keep_scanning = True
        print("Scanning...")

        while keep_scanning:
            for adv in ble.start_scan():
                if adv.complete_name == FRIENDS_NAME:
                    ble.stop_scan()
                    ble.connect(adv)
                    keep_scanning = False

        print("Connected. Done scanning.")
        return uart_service

    else:
        print("Advertising...")
        ble.start_advertising(advertisement)

        while not ble.connected:
            if ble.connected:
                break

        print("Connected. Stop advertising.")
        ble.stop_advertising()

        print("Connecting to Central UART service.")
        for connection in ble.connections:
            if UARTService not in connection:
                continue
            return connection[UARTService]

    return None


# --------------------------
# The main application loop
# --------------------------
while True:
    try:
        # Establish initial connection
        uart = scan_and_connect()

        print("Connected.")

        code = ""
        in_label.text = out_label.text = " " * 18
        edit_label.text = " " * 4
        done = False

        # Run the chat while connected
        while ble.connected:
            button_a.update()
            button_b.update()
            # Check for incoming message
            incoming_bytes = uart.in_waiting
            if incoming_bytes:
                bytes_in = uart.read(incoming_bytes)
                print("Received: ", bytes_in)
                in_label.text = in_label.text[incoming_bytes:] + bytes_in.decode()

            # DOT (or done)
            if button_a.fell:
                start = time.monotonic()
                while time.monotonic() - start < WAIT_FOR_DOUBLE:
                    button_a.update()
                    button_b.update()
                    if button_b.fell:
                        done = True
                if not done and len(code) < 4:
                    print(".", end="")
                    code += "."
                    edit_label.text = "{:4s}".format(code)
                    # time.sleep(0.25)

            # DASH (or done)
            if button_b.fell:
                start = time.monotonic()
                while time.monotonic() - start < WAIT_FOR_DOUBLE:
                    button_a.update()
                    button_b.update()
                    if button_a.fell:
                        done = True
                if not done and len(code) < 4:
                    print("-", end="")
                    code += "-"
                    edit_label.text = "{:4s}".format(code)
                    # time.sleep(DEBOUNCE)

            # Turn Morse Code into letter and send
            if done:
                letter = morse_code.get(code, " ")
                print(" >", letter)
                out_label.text = out_label.text[1:] + letter
                uart.write(str.encode(letter))
                code = ""
                edit_label.text = " " * 4
                done = False
                # time.sleep(DEBOUNCE)

        print("Disconnected.")
    except Exception:
        pass

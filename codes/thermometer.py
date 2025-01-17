import time, displayio, terminalio
from adafruit_circuitplayground import cp
from adafruit_display_text import label
from adafruit_gizmo import tft_gizmo
from adafruit_bitmap_font import bitmap_font
from adafruit_debouncer import Debouncer


display = tft_gizmo.TFT_Gizmo()
courier_2x = bitmap_font.load_font('fonts/Courier-28.pcf')
button_a = Debouncer(lambda: cp.button_a == 0)


# previous iteration button value
old_a_val = cp.button_a

# boolean for current unit type
show_c_units = True

# function to convert celsius degrees to fahrenheit
def c_to_f(c_val):
    return (c_val * 9 / 5) + 32


# Open the background image file
with open("images/240x240.bmp", "rb") as bitmap_file:
    # Setup the file as the bitmap data source
    bitmap = displayio.OnDiskBitmap(bitmap_file)

    # Create a TileGrid to hold the bitmap
    # CircuitPython 6 & 7 compatible
    tile_grid = displayio.TileGrid(
        bitmap,
        pixel_shader=getattr(bitmap, "pixel_shader", displayio.ColorConverter()),
    )
    # CircuitPython 7 compatible only
    # tile_grid = displayio.TileGrid(bitmap, pixel_shader=bitmap.pixel_shader)

    # Create a Group to hold the TileGrid
    temp_group = displayio.Group()

    # Add the TileGrid to the Group
    temp_group.append(tile_grid)

    # variable with initial text value, temperature rounded to 2 places
    text = "%.2f C" % (round(cp.temperature, 2))

    # Create a Group for the text so we can scale it
    text_group = displayio.Group(scale=1, x=120, y=160)

    # Create a Label to show the initial temperature value
    text_area = label.Label(courier_2x, text=text, color=0x5C5C5C)

    # Set the anchor_point for center,top
    text_area.anchor_point = (0.5, 0.0)

    # Set the location to center of display, accounting for text_scale
    text_area.anchored_position = (0, 0)

    # Subgroup for text scaling
    text_group.append(text_area)

    # Add the text_group to main Group
    temp_group.append(text_group)

    # Add the main Group to the Display
    display.root_group = temp_group

    # Loop forever
    while True:
        # button_b.update()
        button_a.update()
        # set current button state to variable
        cur_a_val = cp.button_a
        if cur_a_val and not old_a_val:  # if the button was released
            print("Just released")
            # flip the units boolean to the opposite value
            show_c_units = not show_c_units

        if show_c_units:
            # Update the text
            text_area.text = "%.2f C" % (round(cp.temperature, 2))
        else:  # show f units
            # Update the text
            text_area.text = "%.2f F" % (round(c_to_f(cp.temperature), 2))

        # set previous button value for next time
        old_a_val = cur_a_val
        # Wait a little bit
        time.sleep(0.2)


from types import SimpleNamespace

from ui import FaceDisplay


def pixel(image, point):
    x, y = point
    return tuple(int(channel) for channel in image[y, x])


def test_draws_empty_net_on_dark_background():
    display = FaceDisplay()
    image = display.draw(SimpleNamespace(faces={}))

    assert image.shape == (display.height, display.width, 3)
    assert pixel(image, (1, 1)) == (40, 40, 40)


def test_paints_each_sticker_with_its_color():
    display = FaceDisplay()
    colors = ['W', 'Y', 'G', 'B', 'R', 'O', 'U', 'W', 'Y']
    image = display.draw(SimpleNamespace(faces={'F': colors}))

    offset_x, offset_y = display.face_offsets['F']
    half = display.square_size // 2
    for index, color in enumerate(colors):
        center = (
            offset_x + (index % 3) * display.square_size + half,
            offset_y + (index // 3) * display.square_size + half,
        )
        assert pixel(image, center) == display.color_bgr[color]


def test_unknown_color_falls_back_to_gray():
    display = FaceDisplay()
    image = display.draw(SimpleNamespace(faces={'U': ['?'] * 9}))

    offset_x, offset_y = display.face_offsets['U']
    half = display.square_size // 2
    assert pixel(image, (offset_x + half, offset_y + half)) == (128, 128, 128)

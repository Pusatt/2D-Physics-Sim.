import pygame
import pymunk
import pymunk.pygame_util
import math

# Pygame ayarları
pygame.init()
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("2D Fizik Motoru")
clock = pygame.time.Clock()
fps = 60

# Pymunk uzayı oluştur
space = pymunk.Space()
space.gravity = (0, 900)  # Yerçekimi (x, y)

# Başlangıç değişkenleri
initial_radius = 25
radius = initial_radius
brush_thickness = radius / 5
selected_shape = 1
solid_brush_points = []
# QRKLY yazısı için başlangıç değişkeni
background_text_content = ""
background_color = (0, 0, 0)

# Reset fonksiyonu
def reset_simulation():
    global space, shapes, radius, brush_thickness, selected_shape, text_shapes, solid_brush_points
    space = pymunk.Space()
    space.gravity = (0, 900)
    create_floor(space)
    shapes = []
    text_shapes = []
    solid_brush_points = []
    radius = initial_radius
    brush_thickness = radius / 5
    selected_shape = 1

# Zemin oluştur
def create_floor(space):
    body = pymunk.Body(body_type=pymunk.Body.STATIC)
    body.position = (400, 580)
    shape = pymunk.Segment(body, (-400, 0), (400, 0), 5)
    shape.friction = 0.9  # Sürtünme katsayısı
    space.add(body, shape)

# Nesne oluşturma fonksiyonları
def create_circle(space, pos):
    mass = math.pi * radius**2
    moment = pymunk.moment_for_circle(mass, 0, radius)
    body = pymunk.Body(mass, moment)
    body.position = pos
    shape = pymunk.Circle(body, radius)
    shape.elasticity = 0.8
    shape.density = 1.0
    space.add(body, shape)
    return body, shape

def create_line(space, start_pos, end_pos):
    # Çizginin uzunluğunu hesapla
    dx = end_pos[0] - start_pos[0]
    dy = end_pos[1] - start_pos[1]
    length = math.sqrt(dx**2 + dy**2)

    # Çizgiye kütle ve moment ekle
    mass = length * 0.1  # Kütle uzunlukla orantılı
    moment = pymunk.moment_for_segment(mass, (0, 0), (dx, dy), radius / 5)

    # Dinamik bir gövde oluştur
    body = pymunk.Body(mass, moment)
    body.position = start_pos

    # Segment (çizgi) oluştur
    shape = pymunk.Segment(body, (0, 0), (dx, dy), radius / 5)
    shape.elasticity = 0.8  # Esneklik
    shape.friction = 0.9    # Sürtünme

    # Uzaya ekle
    space.add(body, shape)
    return body, shape

def create_polygon(space, pos, sides):
    vertices = get_regular_polygon_vertices(sides)
    mass = 0.5 * abs(sum(vertices[i][0] * vertices[i-1][1] - vertices[i][1] * vertices[i-1][0] for i in range(len(vertices))))
    moment = pymunk.moment_for_poly(mass, vertices)
    body = pymunk.Body(mass, moment)
    body.position = pos
    shape = pymunk.Poly(body, vertices)
    shape.elasticity = 0.8
    shape.density = 1.0
    space.add(body, shape)
    return body, shape

def create_hollow_circle(space, pos):
    mass = math.pi * (radius**2 - (radius - 3)**2)
    moment = pymunk.moment_for_circle(mass, radius - 3, radius)
    body = pymunk.Body(mass, moment)
    body.position = pos
    outer_circle = pymunk.Circle(body, radius)
    inner_circle = pymunk.Circle(body, radius - 3)
    inner_circle.sensor = True
    outer_circle.elasticity = 0.8
    outer_circle.color = (255, 255, 255, 255)
    inner_circle.color = (0, 0, 0, 0)  # Görünmez yap
    space.add(body, outer_circle)
    return body, outer_circle

def create_text_shape(space, pos, text):
    font = pygame.font.SysFont("Arial", int(radius * 0.8))
    text_surface = font.render(text, True, (255, 255, 255))
    text_width, text_height = text_surface.get_size()
    mass = text_width * text_height * 0.01
    moment = pymunk.moment_for_box(mass, (text_width, text_height))
    body = pymunk.Body(mass, moment)
    body.position = pos
    shape = pymunk.Poly.create_box(body, (text_width, text_height))
    shape.elasticity = 0.8
    space.add(body, shape)
    return body, shape, text_surface

def get_regular_polygon_vertices(sides):
    angle = 2 * math.pi / sides
    return [(math.cos(i * angle) * radius, math.sin(i * angle) * radius) for i in range(sides)]

def finalize_solid_brush(space, points):
    if len(points) > 2:
        center_x = sum(p[0] for p in points) / len(points)
        center_y = sum(p[1] for p in points) / len(points)
        points = [(p[0] - center_x, p[1] - center_y) for p in points]
        mass = 0.5 * abs(sum(points[i][0] * points[i-1][1] - points[i][1] * points[i-1][0] for i in range(len(points))))
        moment = pymunk.moment_for_poly(mass, points)
        body = pymunk.Body(mass, moment)
        body.position = (center_x, center_y)
        shape = pymunk.Poly(body, points)
        shape.elasticity = 0.8
        space.add(body, shape)

create_floor(space)
shapes = []
text_shapes = []

# Çizim için pymunk ayarları
draw_options = pymunk.pygame_util.DrawOptions(screen)

# Çizim değişkenleri
drawing = False
last_position = None
solid_drawing = False

def create_brush_line(space, start_pos, end_pos):
    body = pymunk.Body(body_type=pymunk.Body.STATIC)
    shape = pymunk.Segment(body, start_pos, end_pos, brush_thickness)
    shape.density = 1.0
    shape.friction = 0.9
    space.add(body, shape)

# Ana döngü
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 3:  # Sağ tıklama (çizim başlat)
                drawing = True
                last_position = pymunk.pygame_util.from_pygame(pygame.mouse.get_pos(), screen)
            elif event.button == 1:  # Sol tıklama
                if selected_shape == 0:  # Özel fırça işlevi
                    solid_drawing = True
                    solid_brush_points.append(pymunk.pygame_util.from_pygame(pygame.mouse.get_pos(), screen))
                else:
                    pos = pymunk.pygame_util.from_pygame(event.pos, screen)
                    if selected_shape == 1:
                        shapes.append(create_circle(space, pos))
                    elif selected_shape == 2:
                        start_pos = pymunk.pygame_util.from_pygame(event.pos, screen)
                        end_pos = (start_pos[0] + 50, start_pos[1])  # Çizgi uzunluğunu burada belirleyebilirsin
                        shapes.append(create_line(space, start_pos, end_pos))
                    elif selected_shape == 9:
                        body, shape, text_surface = create_text_shape(space, pos, "Pusat")
                        text_shapes.append((body, text_surface))
                    else:
                        shapes.append(create_polygon(space, pos, selected_shape))
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 3:
                drawing = False
                last_position = None
            elif event.button == 1 and solid_drawing:
                finalize_solid_brush(space, solid_brush_points)
                solid_brush_points = []
                solid_drawing = False
        elif event.type == pygame.MOUSEWHEEL:
            radius = max(5, radius + event.y)
            brush_thickness = radius / 5
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                reset_simulation()
                background_text_content = ""
            elif event.key == pygame.K_q and 'Q' not in background_text_content:
                background_text_content += "Q"
            elif event.key == pygame.K_r and 'R' not in background_text_content:
                background_text_content += "R"
            elif event.key == pygame.K_k and 'K' not in background_text_content:
                background_text_content += "K"
            elif event.key == pygame.K_l and 'L' not in background_text_content:
                background_text_content += "L"
            elif event.key == pygame.K_y and 'Y' not in background_text_content:
                background_text_content += "Y"
            elif pygame.K_0 <= event.key <= pygame.K_9:
                selected_shape = event.key - pygame.K_0

    if drawing:
        current_position = pymunk.pygame_util.from_pygame(pygame.mouse.get_pos(), screen)
        if last_position is not None:
            create_brush_line(space, last_position, current_position)
        last_position = current_position

    if solid_drawing and len(solid_brush_points) > 0:
        current_position = pymunk.pygame_util.from_pygame(pygame.mouse.get_pos(), screen)
        if solid_brush_points[-1] != current_position:
            solid_brush_points.append(current_position)

    # Eğer yazı tam olarak "QRKLY" olursa
    if background_text_content == "QRKLY" and background_color != (255, 255, 255):
        background_color = (255, 255, 255)  # Arkaplan beyaz
        pygame.display.set_caption("QRKLY")  # Uygulama ismini değiştir

    # Ekranı arkaplan rengiyle doldur
    screen.fill(background_color)

    # QRKLY yazısını çiz
    if background_text_content:
        font = pygame.font.SysFont("Arial", 200)
        background_text = font.render(background_text_content, True, (255, 215, 0))
        background_text.set_alpha(15)  # Saydamlık ayarı
        text_rect = background_text.get_rect(center=(400, 220))
        screen.blit(background_text, text_rect)

    # Arkaplana tuş kontrollerini ekle
    font = pygame.font.SysFont("Arial", 20)
    background_text1 = font.render("Sıfırlamak için 'BOŞLUK'", True, (255, 255, 255))
    background_text2 = font.render("Nesne oluşturmak için 'SOL CLICK'", True, (255, 255, 255))
    background_text3 = font.render("Duvar oluşturmak için 'SAĞ CLICK'", True, (255, 255, 255))
    background_text4 = font.render("Seçili cismi değiştirmek için 'SAYI TUŞLARI'", True, (255, 255, 255)) 
    background_text5 = font.render("Seçili cismin boyutunu ayarlamak için 'MOUSE TEKERLEĞİ'", True, (255, 255, 255)) 
    background_text1.set_alpha(100)
    background_text2.set_alpha(100)
    background_text3.set_alpha(100)
    background_text4.set_alpha(100)
    background_text5.set_alpha(100)
    text_rect2 = background_text1.get_rect(center=(400, 335))
    screen.blit(background_text1, text_rect2)
    text_rect2 = background_text2.get_rect(center=(400, 360))
    screen.blit(background_text2, text_rect2)
    text_rect2 = background_text3.get_rect(center=(400, 385))
    screen.blit(background_text3, text_rect2)
    text_rect2 = background_text4.get_rect(center=(400, 410))
    screen.blit(background_text4, text_rect2)
    text_rect2 = background_text5.get_rect(center=(400, 435))
    screen.blit(background_text5, text_rect2)

    space.step(1 / fps)
    space.debug_draw(draw_options)

    # Çizim: Her topun üzerine + işareti ekle
    for body, shape in shapes:
        if isinstance(shape, pymunk.Circle):
            pos = pymunk.pygame_util.to_pygame(body.position, screen)
            pygame.draw.line(screen, (255, 255, 255), (pos[0] - radius // 2, pos[1]), (pos[0] + radius // 2, pos[1]), 2)
            pygame.draw.line(screen, (255, 255, 255), (pos[0], pos[1] - radius // 2), (pos[0], pos[1] + radius // 2), 2)

    # Çizim: "Pusat" metnini düşür
    for body, text_surface in text_shapes:
        pos = pymunk.pygame_util.to_pygame(body.position, screen)
        screen.blit(text_surface, (pos[0] - text_surface.get_width() // 2, pos[1] - text_surface.get_height() // 2))

    # Yarıçap bilgisini ve seçilen cismi ekranda göster
    font = pygame.font.SysFont("Arial", 20)
    radius_text = font.render(f"Yarıçap: {radius}", True, (255, 255, 255))
    shape_text = font.render(f"Cisim: {selected_shape}", True, (255, 255, 255))
    fps_text = font.render(f"FPS: {int(clock.get_fps())}", True, (255, 255, 255))
    screen.blit(radius_text, (10, 10))
    screen.blit(shape_text, (10, 35))
    screen.blit(fps_text, (10, 60))

    pygame.display.flip()
    clock.tick(fps)

pygame.quit()

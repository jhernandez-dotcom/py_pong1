import math
from array import array

import pygame


ANCHO = 800
ALTO = 600
BLANCO = (255, 255, 255)
NEGRO = (0, 0, 0)
FPS = 60


class Paleta:
    def __init__(self, x: int, y: int, ancho: int = 12, alto: int = 100, velocidad: int = 6):
        self.rect = pygame.Rect(x, y, ancho, alto)
        self.velocidad = velocidad

    def mover(self, direccion: int) -> None:
        self.rect.y += direccion * self.velocidad
        self.rect.y = max(0, min(ALTO - self.rect.height, self.rect.y))

    def dibujar(self, pantalla: pygame.Surface) -> None:
        pygame.draw.rect(pantalla, BLANCO, self.rect)


class Pelota:
    def __init__(self, tamano: int = 14, velocidad_base: float = 5.0):
        self.rect = pygame.Rect(0, 0, tamano, tamano)
        self.velocidad_base = velocidad_base
        self.vx = velocidad_base
        self.vy = 0.0
        self.resetear(direccion=1)

    def resetear(self, direccion: int) -> None:
        self.rect.center = (ANCHO // 2, ALTO // 2)
        self.vx = self.velocidad_base * direccion
        self.vy = 0.0

    def actualizar(self) -> None:
        self.rect.x += int(round(self.vx))
        self.rect.y += int(round(self.vy))

    def dibujar(self, pantalla: pygame.Surface) -> None:
        pygame.draw.rect(pantalla, BLANCO, self.rect)


class Juego:
    def __init__(self):
        pygame.init()
        self.pantalla = pygame.display.set_mode((ANCHO, ALTO))
        pygame.display.set_caption("Pong Clásico")
        self.reloj = pygame.time.Clock()

        self.sonido_habilitado = self._inicializar_sonido()
        self.sonido_rebote = self._crear_tono(880, 0.06, 0.30) if self.sonido_habilitado else None
        self.sonido_punto = self._crear_tono(440, 0.18, 0.40) if self.sonido_habilitado else None

        self.paleta_izq = Paleta(30, ALTO // 2 - 50)
        self.paleta_der = Paleta(ANCHO - 42, ALTO // 2 - 50)
        self.pelota = Pelota(velocidad_base=5.0)

        self.puntaje_1 = 0
        self.puntaje_2 = 0
        self.puntaje_objetivo = 5
        self.juego_terminado = False
        self.ganador_texto = ""

        self.fuente_puntaje = pygame.font.SysFont("Arial", 74, bold=True)
        self.fuente_ganador = pygame.font.SysFont("Arial", 54, bold=True)

    def _inicializar_sonido(self) -> bool:
        try:
            pygame.mixer.pre_init(44100, -16, 1, 512)
            pygame.mixer.init()
            return True
        except pygame.error:
            return False

    def _crear_tono(self, frecuencia: int, duracion: float, volumen: float) -> pygame.mixer.Sound:
        tasa_muestreo = 44100
        cantidad_muestras = int(tasa_muestreo * duracion)
        amplitud = int(32767 * max(0.0, min(1.0, volumen)))
        onda = array("h")

        for i in range(cantidad_muestras):
            muestra = int(amplitud * math.sin(2 * math.pi * frecuencia * (i / tasa_muestreo)))
            onda.append(muestra)

        return pygame.mixer.Sound(buffer=onda.tobytes())

    def _dibujar_linea_central(self) -> None:
        ancho_segmento = 6
        alto_segmento = 20
        espacio = 14
        x = ANCHO // 2 - ancho_segmento // 2
        y = 0

        while y < ALTO:
            pygame.draw.rect(self.pantalla, BLANCO, (x, y, ancho_segmento, alto_segmento))
            y += alto_segmento + espacio

    def _dibujar_texto_con_borde(
        self, fuente: pygame.font.Font, texto: str, x: int, y: int, grosor: int = 2
    ) -> None:
        sombra = fuente.render(texto, True, NEGRO)
        for dx in range(-grosor, grosor + 1):
            for dy in range(-grosor, grosor + 1):
                if dx != 0 or dy != 0:
                    self.pantalla.blit(sombra, (x + dx, y + dy))
        superficie = fuente.render(texto, True, BLANCO)
        self.pantalla.blit(superficie, (x, y))

    def _manejar_entrada(self) -> bool:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                return False
            if evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE:
                return False

        teclas = pygame.key.get_pressed()
        if not self.juego_terminado:
            if teclas[pygame.K_w]:
                self.paleta_izq.mover(-1)
            if teclas[pygame.K_s]:
                self.paleta_izq.mover(1)
            if teclas[pygame.K_UP]:
                self.paleta_der.mover(-1)
            if teclas[pygame.K_DOWN]:
                self.paleta_der.mover(1)

        return True

    def _rebotar_con_paleta(self, paleta: Paleta, direccion_horizontal: int) -> None:
        # El ángulo depende del punto de impacto: centro -> ángulo pequeño, extremos -> ángulo mayor.
        centro_paleta = paleta.rect.centery
        distancia_relativa = (self.pelota.rect.centery - centro_paleta) / (paleta.rect.height / 2)
        distancia_relativa = max(-1.0, min(1.0, distancia_relativa))
        angulo_max = math.radians(60)
        angulo = distancia_relativa * angulo_max

        self.pelota.vx = direccion_horizontal * self.pelota.velocidad_base * math.cos(angulo)
        self.pelota.vy = self.pelota.velocidad_base * math.sin(angulo)

    def _actualizar_juego(self) -> None:
        if self.juego_terminado:
            return

        self.pelota.actualizar()

        # Reflexión vertical clásica al tocar techo o suelo.
        if self.pelota.rect.top <= 0:
            self.pelota.rect.top = 0
            self.pelota.vy *= -1
        elif self.pelota.rect.bottom >= ALTO:
            self.pelota.rect.bottom = ALTO
            self.pelota.vy *= -1

        if self.pelota.rect.colliderect(self.paleta_izq.rect) and self.pelota.vx < 0:
            self.pelota.rect.left = self.paleta_izq.rect.right
            self._rebotar_con_paleta(self.paleta_izq, direccion_horizontal=1)
            if self.sonido_rebote:
                self.sonido_rebote.play()

        if self.pelota.rect.colliderect(self.paleta_der.rect) and self.pelota.vx > 0:
            self.pelota.rect.right = self.paleta_der.rect.left
            self._rebotar_con_paleta(self.paleta_der, direccion_horizontal=-1)
            if self.sonido_rebote:
                self.sonido_rebote.play()

        if self.pelota.rect.left <= 0:
            self.puntaje_2 += 1
            if self.sonido_punto:
                self.sonido_punto.play()
            self._reiniciar_despues_de_punto(anotador=2)

        if self.pelota.rect.right >= ANCHO:
            self.puntaje_1 += 1
            if self.sonido_punto:
                self.sonido_punto.play()
            self._reiniciar_despues_de_punto(anotador=1)

        if self.puntaje_1 >= self.puntaje_objetivo:
            self.juego_terminado = True
            self.ganador_texto = "¡Jugador 1 GANA!"
        elif self.puntaje_2 >= self.puntaje_objetivo:
            self.juego_terminado = True
            self.ganador_texto = "¡Jugador 2 GANA!"

    def _reiniciar_despues_de_punto(self, anotador: int) -> None:
        direccion_salida = 1 if anotador == 1 else -1
        self.pelota.resetear(direccion=direccion_salida)
        self.dibujar()
        pygame.display.flip()
        pygame.time.delay(500)

    def dibujar(self) -> None:
        self.pantalla.fill(NEGRO)
        self._dibujar_linea_central()

        self.paleta_izq.dibujar(self.pantalla)
        self.paleta_der.dibujar(self.pantalla)
        self.pelota.dibujar(self.pantalla)

        texto_1 = str(self.puntaje_1)
        texto_2 = str(self.puntaje_2)

        self._dibujar_texto_con_borde(self.fuente_puntaje, texto_1, ANCHO // 2 - 150, 20)
        self._dibujar_texto_con_borde(self.fuente_puntaje, texto_2, ANCHO // 2 + 100, 20)

        if self.juego_terminado:
            superficie = self.fuente_ganador.render(self.ganador_texto, True, BLANCO)
            rect = superficie.get_rect(center=(ANCHO // 2, ALTO // 2))
            self.pantalla.blit(superficie, rect)

    def ejecutar(self) -> None:
        ejecutando = True
        while ejecutando:
            self.reloj.tick(FPS)
            ejecutando = self._manejar_entrada()
            self._actualizar_juego()
            self.dibujar()
            pygame.display.flip()

        pygame.quit()


if __name__ == "__main__":
    Juego().ejecutar()

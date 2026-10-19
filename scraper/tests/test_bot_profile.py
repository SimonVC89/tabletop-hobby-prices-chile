"""El aviso de demora del bot y los limites de su perfil publico."""

from src import setup_bot_profile as profile
from src.telegram_subscribers import DELAY_NOTICE, HELP_TEXT


def test_el_aviso_de_demora_dice_horas_y_no_minutos():
    assert "varias horas" in DELAY_NOTICE
    assert "15 minutos" not in DELAY_NOTICE


def test_la_ayuda_incluye_el_aviso():
    assert DELAY_NOTICE in HELP_TEXT


def test_la_descripcion_visible_antes_de_iniciar_avisa_de_la_demora():
    """Es lo unico que se lee antes de esperar una respuesta."""
    assert "demora" in profile.DESCRIPTION and "horas" in profile.DESCRIPTION
    assert "demora" in profile.SHORT_DESCRIPTION.lower()


def test_los_textos_del_perfil_respetan_los_limites_de_telegram():
    profile.validate()  # lanza AssertionError si algun texto se pasa


def test_el_menu_de_comandos_cubre_los_comandos_del_bot():
    registered = {name for name, _ in profile.COMMANDS}
    assert {"start", "stop", "seguir", "siguiendo", "dar_de_baja", "ayuda"} <= registered

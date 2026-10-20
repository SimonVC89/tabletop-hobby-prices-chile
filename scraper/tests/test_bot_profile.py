"""Perfil publico del bot: limites de Telegram y menu de comandos."""

from src import setup_bot_profile as profile


def test_la_descripcion_ya_no_avisa_de_demora():
    """Con el webhook las respuestas son inmediatas: el aviso de horas de demora seria falso."""
    assert "demora" not in profile.DESCRIPTION.lower()
    assert "demora" not in profile.SHORT_DESCRIPTION.lower()


def test_los_textos_del_perfil_respetan_los_limites_de_telegram():
    profile.validate()  # lanza AssertionError si algun texto se pasa


def test_el_menu_de_comandos_cubre_los_comandos_del_bot():
    registered = {name for name, _ in profile.COMMANDS}
    assert {"start", "stop", "seguir", "siguiendo", "dar_de_baja", "ayuda"} <= registered

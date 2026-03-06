from html import escape

from src.keyboards.ai import MODE_IMAGE_TEXT, MODE_LLM_TEXT, MODE_VIDEO_TEXT
from src.core.schemas import AIModelItem


class AIFlowHelper:
    MODE_TEXT_TO_TYPE = {
        MODE_LLM_TEXT: "llm",
        MODE_VIDEO_TEXT: "video",
        MODE_IMAGE_TEXT: "image",
    }

    @staticmethod
    def serialize_models(models: list[AIModelItem]) -> list[dict]:
        return [model.model_dump(mode="json") for model in models]

    @staticmethod
    def deserialize_models(raw_models: list[dict]) -> list[AIModelItem]:
        return [AIModelItem.model_validate(model) for model in raw_models]

    @staticmethod
    def render_models_text(models: list[AIModelItem], current_model_name: str | None) -> str:
        lines = [
            f"текущая модель: <b>{escape(current_model_name or 'не выбрана')} ✅</b>",
            "Список доступных нейросетей:",
            "",
            "<blockquote>",
        ]
        for model in models:
            description = model.description or ""
            lines.append(f"• <b>{escape(model.name)}</b>")
            lines.append(f"  {escape(description)}")
            lines.append("")
        lines.append("</blockquote>")
        return "\n".join(lines).rstrip()

    @staticmethod
    def render_llm_config_text(
        temperature: float | None,
        instructions: str | None,
    ) -> str:
        temperature_value = str(temperature) if temperature is not None else "не задана"
        instructions_value = instructions.strip() if instructions else "не заданы"
        if len(instructions_value) > 280:
            instructions_value = f"{instructions_value[:280]}..."

        return "\n".join(
            [
                "<b>Настройка инструкции для ИИ</b>",
                "",
                "<b>Параметры:</b>",
                "• <b>Температура</b> — креативность ответа. Ниже = стабильнее, выше = разнообразнее.",
                "• <b>Инструкции</b> — постоянный стиль и правила ответа модели.",
                "",
                "<b>Пример:</b>",
                "<blockquote>Ты лаконичный помощник. Отвечай по делу и списками.</blockquote>",
                "",
                f"Текущая температура: <b>{escape(temperature_value)}</b>",
                f"Текущие инструкции: <blockquote>{escape(instructions_value)}</blockquote>",
            ]
        )

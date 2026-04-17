from uuid import UUID

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends, HTTPException

from src.api.dependencies import (
    TgRateLimiter,
    require_api_key,
    resolve_whitelisted_user_id_by_telegram_id,
)
from src.exceptions.payment import (
    PaymentConflictError,
    PaymentNotFoundError,
    PaymentProcessingError,
    PaymentProviderRequestError,
    PaymentProviderUnavailableError,
    PaymentValidationError,
)
from src.schemas.billing import (
    InvoiceCreateRequestSchema,
    InvoiceCreateResponseSchema,
    PaymentMethodOptionSchema,
    PaymentMethodsResponseSchema,
    PaymentProductsResponseSchema,
    PaymentProductItemSchema,
)
from src.services.invoice import PaymentInvoiceService

router = APIRouter(
    prefix="/invoice",
    route_class=DishkaRoute,
    dependencies=[Depends(require_api_key)],
)


@router.post(
    "",
    response_model=InvoiceCreateResponseSchema,
    dependencies=[
        Depends(TgRateLimiter(limit=10, window_seconds=60, path_name_key="invoice_create"))
    ],
)
async def create_invoice(
    payload: InvoiceCreateRequestSchema,
    service: FromDishka[PaymentInvoiceService],
    user_id: UUID = Depends(resolve_whitelisted_user_id_by_telegram_id),
) -> InvoiceCreateResponseSchema:
    try:
        return await service.create_invoice(user_id=user_id, payload=payload)
    except (
        PaymentValidationError,
        PaymentProcessingError,
        PaymentProviderRequestError,
    ) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except PaymentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PaymentConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except PaymentProviderUnavailableError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

@router.get(
    "/methods",
    response_model=PaymentMethodsResponseSchema,
    dependencies=[
        Depends(TgRateLimiter(limit=20, window_seconds=60, path_name_key="invoice_methods"))
    ],
)
async def list_payment_methods(
    service: FromDishka[PaymentInvoiceService],
    _user_id: UUID = Depends(resolve_whitelisted_user_id_by_telegram_id),
) -> PaymentMethodsResponseSchema:
    methods = await service.list_payment_methods()
    return PaymentMethodsResponseSchema(
        methods=[
            PaymentMethodOptionSchema(
                code=method.method_code,
                enabled=method.enabled,
                is_soon=method.is_soon,
            )
            for method in methods
        ]
    )


@router.get(
    "/products",
    response_model=PaymentProductsResponseSchema,
    dependencies=[
        Depends(TgRateLimiter(limit=20, window_seconds=60, path_name_key="invoice_products"))
    ],
)
async def list_payment_products(
    service: FromDishka[PaymentInvoiceService],
    _user_id: UUID = Depends(resolve_whitelisted_user_id_by_telegram_id),
) -> PaymentProductsResponseSchema:
    products = await service.list_payment_products()
    return PaymentProductsResponseSchema(
        products=[
            PaymentProductItemSchema(
                plan_id=item.plan_id,
                tariff_code=item.tariff_code,
                name=item.name,
                display_name=item.display_name,
                description=item.description,
                billing_interval=item.billing_interval,
                duration_days=item.duration_days,
                price_rub=item.price_rub,
                tokens_amount=item.tokens_amount,
                is_vpn_bonus_enabled=item.is_vpn_bonus_enabled,
            )
            for item in products
        ]
    )

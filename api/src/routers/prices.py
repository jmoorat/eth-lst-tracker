from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from data_access import prices as price_data
from database import get_db
from schemas.price import (
    AdvancedPriceHistoryResponse,
    AdvancedPriceResponse,
    FullPriceResponse,
    PriceHistoryResolutionRequest,
    PriceHistoryResponse,
    PriceHistoryStats,
    PriceResponse,
    TokenNetworkResponse,
    resolution_request_to_time_bucket,
)

router = APIRouter(tags=["prices"])


@router.get("/prices")
def get_last_prices(db: Session = Depends(get_db)) -> list[FullPriceResponse]:
    last_prices = price_data.get_last_prices(db)
    return [FullPriceResponse(**r) for r in last_prices]


@router.get("/prices/{token_name}/history")
def get_price_history(
    token_name: str,
    network: str = "ethereum",
    primary_market: bool = False,
    resolution: PriceHistoryResolutionRequest = PriceHistoryResolutionRequest.ONE_DAY,
    db: Session = Depends(get_db),
) -> PriceResponse:
    if primary_market and network != "ethereum":
        raise HTTPException(status_code=400, detail="Primary market is only available on Ethereum")

    result = price_data.get_price_history(
        db,
        token_name,
        network,
        primary_market,
        False,
        resolution_request_to_time_bucket[resolution],
    )

    response: PriceResponse = PriceResponse(
        token_name=token_name,
        network=network,
        is_primary_market=primary_market,
        prices=[
            PriceHistoryResponse(
                timestamp=r["time_bucket"],
                price_eth=r["price_eth"],
                premium_percentage=r["premium_percentage"],
            )
            for r in result
        ],
    )

    return response


@router.get("/prices/{token_name}/history/advanced")
def get_advanced_price_history(
    token_name: str,
    network: str = "ethereum",
    primary_market: bool = False,
    resolution: PriceHistoryResolutionRequest = PriceHistoryResolutionRequest.ONE_DAY,
    db: Session = Depends(get_db),
) -> AdvancedPriceResponse:
    if primary_market and network != "ethereum":
        raise HTTPException(status_code=400, detail="Primary market is only available on Ethereum")

    result = price_data.get_price_history(
        db,
        token_name,
        network,
        primary_market,
        True,
        resolution_request_to_time_bucket[resolution],
    )

    response: AdvancedPriceResponse = AdvancedPriceResponse(
        token_name=token_name,
        network=network,
        is_primary_market=primary_market,
        prices=[
            AdvancedPriceHistoryResponse(
                timestamp=r["time_bucket"],
                price_eth=PriceHistoryStats(
                    min=r["min_price_eth"],
                    max=r["max_price_eth"],
                    avg=r["avg_price_eth"],
                    first=r["first_price_eth"],
                    last=r["last_price_eth"],
                ),
                premium_percentage=PriceHistoryStats(
                    min=r["min_premium_percentage"],
                    max=r["max_premium_percentage"],
                    avg=r["avg_premium_percentage"],
                    first=r["first_premium_percentage"],
                    last=r["last_premium_percentage"],
                ),
            )
            for r in result
        ],
    )

    return response


@router.get("/prices/{token_name}/last")
def get_last_price(
    token_name: str,
    network: str = "ethereum",
    primary_market: bool = False,
    db: Session = Depends(get_db),
) -> FullPriceResponse:
    if primary_market and network != "ethereum":
        raise HTTPException(status_code=400, detail="Primary market is only available on Ethereum")

    last_price = price_data.get_last_price(db, token_name, network, primary_market)
    if not last_price:
        raise HTTPException(status_code=404, detail="Item not found")

    return FullPriceResponse(
        token_name=token_name,
        network=network,
        is_primary_market=primary_market,
        **last_price,
    )


@router.get("/tokens")
def get_available_tokens(db: Session = Depends(get_db)) -> list[TokenNetworkResponse]:
    result = price_data.get_available_tokens_and_networks(db)
    return result

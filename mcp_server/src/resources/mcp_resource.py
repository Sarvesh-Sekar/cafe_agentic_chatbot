from src.routers.mcp_router import router 

@router.resource("resource://get_info")
async def get_prepare_info() -> str:
    """
    Returns the common methodology and guidelines for preparing 
    standard coffee types (Espresso, Latte, Mocha, Cold Brew).
    """

    return """
    # Common Coffee Preparation Methodology
    
    ## 1. Core Principles
    - **Grind Size is Critical**: 
        - Fine for Espresso/Mocha (high pressure, fast extraction).
        - Coarse for Cold Brew (low temperature, long extraction).
    - **Temperature Control**: 
        - Hot Brews: Aim for 195°F–205°F (90°C–96°C).
        - Cold Brews: Room temperature or refrigerated (never heat).
    
    ## 2. Standard Recipes & Ratios
    - **Espresso**: 18-20g fine grounds yielded to 36-40g liquid in 25-30 seconds.
    - **Latte**: 1 shot espresso + 1:3 ratio of steamed milk + thin layer of microfoam.
    - **Mocha**: 1 shot espresso + 1-2 tsp cocoa/chocolate syrup + steamed milk.
    - **Cold Brew**: 1:4 (concentrate) or 1:8 (ready-to-drink) ratio of coarse grounds to water; steep for 12-24 hours.

    ## 3. General Workflow
    1. **Measure**: Use a scale for precision (grams over volume).
    2. **Saturate**: Ensure all grounds are evenly wet (blooming for hot, stirring for cold).
    3. **Extract**: Follow specific time intervals for the chosen method.
    4. **Filter**: Remove grounds cleanly to prevent over-extraction/bitterness.
    """

@router.resource("resource://get_policy_info")
async def get_policy_info() -> str:
    """Provides the official Bean & Brew policy for online and offline orders."""
    return """
    # Bean & Brew Ordering Policies

    ## 1. Online Orders (App/Web)
    - **Preparation**: Starts immediately after payment confirmation.
    - **Pickup Window**: Orders must be collected within 30 minutes of the "Ready" notification. 
    - **Cancellations**: Full refund if cancelled within 2 minutes of placing; no refund once preparation begins.
    - **Modifications**: Not permitted once the order is sent to the kitchen.

    ## 2. Offline Orders (In-Store)
    - **Payment**: Required at the time of ordering (Cash, Card, or Digital Wallet).
    - **Seating**: First-come, first-served basis; ordering does not guarantee a table.
    - **Refills**: One free refill on "House Blend" drip coffee with a valid same-day receipt.

    ## 3. General Rules
    - **Dietary Requests**: Please inform staff of allergies before ordering.
    - **Returns**: If an item is prepared incorrectly, we will replace it immediately at no extra cost.
    """


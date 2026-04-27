"""Core functionality for Meta Ads API MCP package."""

from . import (
    ads_library,  # Import module to register conditional tools
    authentication,  # Import module to register conditional auth tools
    reports,  # Import module to register conditional tools
)
from .accounts import get_account_info, get_ad_accounts
from .ads import get_ad_creatives, get_ad_details, get_ad_image, get_ads, get_creative_details, update_ad
from .adsets import get_adset_details, get_adsets, update_adset
from .auth import login
from .budget_schedules import create_budget_schedule
from .campaigns import create_campaign, get_campaign_details, get_campaigns
from .insights import get_insights
from .openai_deep_research import fetch, search  # OpenAI MCP Deep Research tools
from .server import login_cli, main, mcp_server
from .targeting import (
    estimate_audience_size,
    get_interest_suggestions,
    search_behaviors,
    search_demographics,
    search_geo_locations,
    search_interests,
)

__all__ = [
    "mcp_server",
    "get_ad_accounts",
    "get_account_info",
    "get_campaigns",
    "get_campaign_details",
    "create_campaign",
    "get_adsets",
    "get_adset_details",
    "update_adset",
    "get_ads",
    "get_ad_details",
    "get_creative_details",
    "get_ad_creatives",
    "get_ad_image",
    "update_ad",
    "get_insights",
    # Note: 'get_login_link' is registered conditionally by the authentication module
    "login_cli",
    "login",
    "main",
    "create_budget_schedule",
    "search_interests",
    "get_interest_suggestions",
    "estimate_audience_size",
    "search_behaviors",
    "search_demographics",
    "search_geo_locations",
    "search",  # OpenAI MCP Deep Research search tool
    "fetch",  # OpenAI MCP Deep Research fetch tool
]

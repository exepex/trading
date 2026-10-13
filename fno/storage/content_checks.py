"""The content check of each raw dataset (stories A1, A8, P6): a function of a file's name and bytes that raises
BadFile (a ValueError) when the file is damaged or not in its publisher's layout. The coverage check, the librarian
and the snapshot takers use the same checks."""

from __future__ import annotations

from ..constants import INDEX_INDIA_VIX, INDEX_NIFTY_50
from ..fo_bhavcopy import BadFile, read_fo_file, read_index_closes
from ..market_read_models.corporate_actions import read_corporate_actions
from ..market_read_models.nse_files import read_delivery, read_equity_bhavcopy, read_equity_list, read_nifty500_list
from ..research_data.participant_oi import read_participant_oi
from .raw_source import (
    NseDailyFoSource,
    NseDeliverySource,
    NseEquityBhavcopySource,
    NseIndexCloseSource,
    NseLegacyFoSource,
    ParticipantOiSource,
)
from .snapshot_source import (
    CorporateActionsBySymbolSource,
    CorporateActionsSource,
    EquityListSource,
    Nifty500ListSource,
)

REQUIRED_INDICES = (INDEX_NIFTY_50, INDEX_INDIA_VIX)


def validate_index_close(filename: str, data: bytes) -> None:
    missing = [name for name in REQUIRED_INDICES if name not in read_index_closes(data, filename)]
    if missing:
        raise BadFile(f"{filename}: no closing value for {missing}")


def validate_participant_oi(filename: str, data: bytes) -> None:
    read_participant_oi(data, filename, ParticipantOiSource.day_for(filename))


VALIDATORS = {
    NseLegacyFoSource: read_fo_file,
    NseDailyFoSource: read_fo_file,
    NseIndexCloseSource: validate_index_close,
    ParticipantOiSource: validate_participant_oi,
    NseEquityBhavcopySource: lambda filename, data: read_equity_bhavcopy(data, filename),
    NseDeliverySource: lambda filename, data: read_delivery(data, filename),
    EquityListSource: lambda filename, data: read_equity_list(data, filename),
    Nifty500ListSource: lambda filename, data: read_nifty500_list(data, filename),
    CorporateActionsSource: lambda filename, data: read_corporate_actions(data, filename),
    CorporateActionsBySymbolSource: lambda filename, data: read_corporate_actions(data, filename),
}

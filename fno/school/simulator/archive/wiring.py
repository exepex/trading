"""Composition root of the practice archive (story MS-SIM-e2): O9's data store on the owner's Drive, the receipt
publisher on the run's own receipts folder, and the verified Drive cache for the read-back. The publisher's recorder
commits only `receipts/data/school-practice/<run id>/`, so a practice commit can never carry another file."""

import os

from ....storage.data_wiring import DATA_AREA, REPOSITORY, build_data_store, build_drive_cache, receipt_folder
from ....storage.manifest_commit import GitManifestRecorder
from ....storage.receipt_publisher import GitReceiptPublisher
from ...dashcam.reader import VerifiedDriveReader
from .archive import PracticeArchive
from .names import receipts_folder

WRITER = "school practice"
RECEIPTS_MESSAGE = "Receipts: school practice run ({what})"
RECEIPTS_LABEL = "practice receipts"


def build_practice_archive(run: str, env=os.environ) -> PracticeArchive:
    data = build_data_store(WRITER, run, env)
    recorder = GitManifestRecorder(REPOSITORY, REPOSITORY / receipts_folder(run), message=RECEIPTS_MESSAGE,
                                   label=RECEIPTS_LABEL)  # fmt: skip
    publisher = GitReceiptPublisher(recorder, receipt_folder(), REPOSITORY)
    return PracticeArchive(data, publisher, VerifiedDriveReader(build_drive_cache(env), DATA_AREA))

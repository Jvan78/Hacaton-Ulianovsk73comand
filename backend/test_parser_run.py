from app.parser import normalize_row
example = {
    "SHR": "(SHR-ZZZZZ\n-ULSF0700\n-DOF/250101 ... SID/7772271624)",
    "DEP": "-TITLE IDEP\n-ATD 0715\n-ADEPZ 593601N0285056E\n-PAP 0",
    "ARR": "-TITLE IARR\n-ATA 1636\n-ADARR 593601N0285056E"
}
print(normalize_row(example))

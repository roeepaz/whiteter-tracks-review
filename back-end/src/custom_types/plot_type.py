from dataclasses import dataclass
from typing import Optional

@dataclass
class Plot:
    system_id: int
    plot_id: int
    t: float
    x: float
    y: float
    z: float
    sig_x: Optional[float] = None
    sig_y: Optional[float] = None
    sig_z: Optional[float] = None
    target_id: Optional[int] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    altitude: Optional[float] = None
    STN: Optional[str] = None

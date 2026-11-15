from sqlalchemy import String, Double, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from src.config.database import Base
class Approval(Base):
    __tablename__ = 'approvals'
    id: Mapped[int] = mapped_column(primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey('jobs.id'))
    reviewer_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    reviewer_name: Mapped[str] = mapped_column(String(80))
    reviewer_email: Mapped[str] = mapped_column(String(150))
    action: Mapped[str] = mapped_column(String(20))  # approve 同意 / withdraw 撤回 / legacy 历史凭据
    created_at: Mapped[float] = mapped_column(Double)

from sqlalchemy import Date, Integer, String, case, cast, func, literal, select
from sqlalchemy.sql.elements import ColumnElement
from app.models import Notification, User
from app import constants
from datetime import date


def group_subkey() -> ColumnElement[str]:
    return func.coalesce(
        case(
            (
                Notification.notification_type.in_(
                    constants.NOTIFICATION_VOTE_TYPES
                ),
                cast(
                    func.sign(
                        cast(Notification.data["user_score"].astext, Integer)
                    ),
                    String,
                ),
            ),
            (
                Notification.notification_type
                == constants.NOTIFICATION_SCHEDULE_ANIME,
                Notification.data["slug"].astext,
            ),
            (
                Notification.notification_type
                == constants.NOTIFICATION_THIRDPARTY_LOGIN,
                Notification.data["client"]["reference"].astext,
            ),
            (
                Notification.notification_type
                == constants.NOTIFICATION_HIKKA_UPDATE,
                cast(Notification.id, String),
            ),
            else_=literal(""),
        ),
        literal(""),
    )


def group_day() -> ColumnElement[date]:
    # Created is naive UTC: tag it as UTC, then take the wall-clock date in Kyiv
    return cast(
        func.timezone(
            constants.NOTIFICATION_GROUP_TIMEZONE,
            func.timezone("UTC", Notification.created),
        ),
        Date,
    )


def group_actor() -> ColumnElement[str | None]:
    """Who triggered a member, as a stable account id so renames do not split it

    Rows older than initiator_user_id only store a username: resolve it to
    the account that holds it now, else count the stored handle. Downvotes are
    anonymous and add no actors, even older rows that still store the voter.
    """

    stored_username = Notification.data["username"].astext
    legacy_user_id = (
        select(User.id)
        .where(User.username == stored_username)
        .limit(1)
        .scalar_subquery()
    )

    return case(
        (
            Notification.notification_type.in_(
                constants.NOTIFICATION_VOTE_TYPES
            )
            & (cast(Notification.data["user_score"].astext, Integer) < 0),
            None,
        ),
        # COALESCE stops at the first non-null, so new rows skip the lookup
        else_=func.coalesce(
            cast(Notification.initiator_user_id, String),
            cast(legacy_user_id, String),
            stored_username,
        ),
    )


def group_target() -> ColumnElement[str | None]:
    """What a member points at, so group can say "3 comments" vs "comment"

    Replies have no target: their data names the thread root,
    not the replied-to comment.
    """

    return case(
        (
            Notification.notification_type.in_(
                [
                    constants.NOTIFICATION_COMMENT_VOTE,
                    constants.NOTIFICATION_COMMENT_TAG,
                ]
            ),
            Notification.data["comment_reference"].astext,
        ),
        (
            Notification.notification_type.in_(
                [
                    constants.NOTIFICATION_COLLECTION_VOTE,
                    constants.NOTIFICATION_ARTICLE_VOTE,
                    constants.NOTIFICATION_SCHEDULE_ANIME,
                ]
            ),
            Notification.data["slug"].astext,
        ),
        (
            Notification.notification_type.in_(
                constants.NOTIFICATION_EDIT_TYPES
            ),
            Notification.data["edit_id"].astext,
        ),
        else_=None,
    )


def make_group_reference(notification_type: str, subkey: str, day: date) -> str:
    return f"{notification_type}:{subkey}:{day.isoformat()}"


def parse_group_reference(reference: str) -> tuple[str, str, str] | None:
    """Split reference into type, subkey and ISO day or None if malformed"""

    head, sep, day = reference.rpartition(":")
    notification_type, sep2, subkey = head.partition(":")

    if not sep or not sep2:
        return None

    if notification_type not in constants.NOTIFICATION_TYPES:
        return None

    return notification_type, subkey, day

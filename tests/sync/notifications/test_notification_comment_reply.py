from app.sync.notifications import generate_notifications
from client_requests import request_comments_write
from app.models import Notification
from sqlalchemy import select, func
from app import constants


async def test_notification_comment_reply(
    client,
    aggregator_anime,
    aggregator_anime_info,
    create_dummy_user,
    create_test_user,
    get_dummy_token,
    get_test_token,
    test_session,
):
    # Write top level comment
    response = await request_comments_write(
        client, get_dummy_token, "edit", "17", "First comment, yay!"
    )

    # Write reply to top level comment
    parent_comment = response.json()["reference"]
    response = await request_comments_write(
        client, get_test_token, "edit", "17", "Reply", parent_comment
    )

    # Generate notifications
    await generate_notifications(test_session)

    # Make sure there is only one notification
    notificaitons_count = await test_session.scalar(
        select(func.count(Notification.id)).filter(
            Notification.notification_type
            == constants.NOTIFICATION_COMMENT_REPLY
        )
    )
    assert notificaitons_count == 1

    # Get comment reply notification
    notificaiton = await test_session.scalar(
        select(Notification).filter(
            Notification.user_id == create_dummy_user.id
        )
    )

    # And make sure it's correct
    notification_type = constants.NOTIFICATION_COMMENT_REPLY
    assert notificaiton.notification_type == notification_type
    assert notificaiton.user_id == create_dummy_user.id
    assert notificaiton.data["content_type"] == "edit"
    assert notificaiton.data["slug"] == "17"


async def test_notification_comment_reply_same_author(
    client,
    aggregator_anime,
    aggregator_anime_info,
    create_test_user,
    get_test_token,
    test_session,
):
    # Write top level comment
    response = await request_comments_write(
        client, get_test_token, "edit", "17", "First comment, yay!"
    )

    # Write reply to top level comment by same user
    parent_comment = response.json()["reference"]
    response = await request_comments_write(
        client, get_test_token, "edit", "17", "Reply", parent_comment
    )

    # Generate notifications
    await generate_notifications(test_session)

    # Make sure there are not reply notification
    notifications_count = await test_session.scalar(
        select(func.count(Notification.id)).filter(
            Notification.notification_type
            == constants.NOTIFICATION_COMMENT_REPLY
        )
    )

    assert notifications_count == 0

"""initial

Revision ID: 7c109e020a2a
Revises: 
Create Date: 2022-04-15 19:17:18.279123

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7c109e020a2a'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('tag',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('tag', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('id')
    )
    op.create_table('user',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('username', sa.String(length=64), nullable=True),
    sa.Column('email', sa.String(length=120), nullable=True),
    sa.Column('password_hash', sa.String(length=128), nullable=True),
    sa.Column('img_path', sa.String(length=64), nullable=True),
    sa.Column('img_uuid', sa.String(length=64), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_user_email'), ['email'], unique=True)
        batch_op.create_index(batch_op.f('ix_user_img_uuid'), ['img_uuid'], unique=False)
        batch_op.create_index(batch_op.f('ix_user_username'), ['username'], unique=True)

    op.create_table('course',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=64), nullable=True),
    sa.Column('author_id', sa.Integer(), nullable=True),
    sa.Column('desc', sa.Text(), nullable=False),
    sa.Column('rating', sa.Integer(), nullable=True),
    sa.Column('short_desc', sa.Text(), nullable=False),
    sa.Column('img_path', sa.String(length=64), nullable=True),
    sa.Column('img_uuid', sa.String(length=64), nullable=True),
    sa.Column('is_published', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['author_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('course', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_course_img_uuid'), ['img_uuid'], unique=False)
        batch_op.create_index(batch_op.f('ix_course_name'), ['name'], unique=True)

    op.create_table('post',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=64), nullable=True),
    sa.Column('text', sa.Text(), nullable=True),
    sa.Column('author_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['author_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('courses_tags',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('course_id', sa.Integer(), nullable=True),
    sa.Column('tag_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['course_id'], ['course.id'], ),
    sa.ForeignKeyConstraint(['tag_id'], ['tag.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('id')
    )
    op.create_table('lesson',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=64), nullable=True),
    sa.Column('course_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['course_id'], ['course.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('my_courses',
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('course_id', sa.Integer(), nullable=False),
    sa.Column('completed', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['course_id'], ['course.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('user_id', 'course_id')
    )
    op.create_table('lesson_file',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('path', sa.String(length=64), nullable=True),
    sa.Column('uuid', sa.String(length=64), nullable=True),
    sa.Column('name', sa.String(length=64), nullable=True),
    sa.Column('lesson_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['lesson_id'], ['lesson.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('lesson_file', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_lesson_file_name'), ['name'], unique=False)
        batch_op.create_index(batch_op.f('ix_lesson_file_uuid'), ['uuid'], unique=False)

    op.create_table('page',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('text', sa.Text(), nullable=True),
    sa.Column('lesson_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['lesson_id'], ['lesson.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('task_check',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('page_id', sa.Integer(), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('file', sa.String(length=64), nullable=True),
    sa.Column('date', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['page_id'], ['page.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('task_check')
    op.drop_table('page')
    with op.batch_alter_table('lesson_file', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_lesson_file_uuid'))
        batch_op.drop_index(batch_op.f('ix_lesson_file_name'))

    op.drop_table('lesson_file')
    op.drop_table('my_courses')
    op.drop_table('lesson')
    op.drop_table('courses_tags')
    op.drop_table('post')
    with op.batch_alter_table('course', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_course_name'))
        batch_op.drop_index(batch_op.f('ix_course_img_uuid'))

    op.drop_table('course')
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_user_username'))
        batch_op.drop_index(batch_op.f('ix_user_img_uuid'))
        batch_op.drop_index(batch_op.f('ix_user_email'))

    op.drop_table('user')
    op.drop_table('tag')
    # ### end Alembic commands ###

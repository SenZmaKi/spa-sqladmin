### Basic example

You might need to add custom views to the existing SQLAdmin views, for example to create dashboards, show custom info or add new API endpoints.

To add custom views to the Admin interface, you can use the `BaseView` included in SQLAdmin. Here's an example to add custom views:

!!! example

    ```python
    from spa_sqladmin import BaseView, expose
    from starlette.responses import JSONResponse

    class ReportView(BaseView):
        name = "Report Page"
        icon = "TrendingUp"

        @expose("/report", methods=["GET"])
        async def report_page(self, request):
            return JSONResponse({"message": "Report data here"})

    admin.add_view(ReportView)
    ```

Now visiting `/admin/report` will return the JSON response.

It is also possible to use the expose decorator to add extra endpoints to a ModelView. 
The `path` is in this case prepended with the view's identity, in this case `/admin/user/profile/{pk}`.

!!! example

    ```python
    from spa_sqladmin import ModelView, expose
    from starlette.responses import JSONResponse

    class UserView(ModelView):

        @expose("/profile/{pk}", methods=["GET"])
        async def profile(self, request):
            user = await self.get_object_for_edit(request)
            return JSONResponse({"user_id": user.id, "name": user.name})

    admin.add_view(UserView)
    ```

### Database access

The example above was very basic and you probably want to access database and SQLAlchemy models in your custom view. You can use `sessionmaker` the same way SQLAdmin is using it to do so:

!!! example

    ```python
    from sqlalchemy import Column, Integer, String, select, func
    from sqlalchemy.orm import sessionmaker, declarative_base
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
    from spa_sqladmin import Admin, BaseView, expose
    from starlette.applications import Starlette
    from starlette.responses import JSONResponse

    Base = declarative_base()
    engine = create_async_engine("sqlite+aiosqlite:///test.db")
    Session = sessionmaker(bind=engine, class_=AsyncSession)

    app = Starlette()
    admin = Admin(app=app, engine=engine)


    class User(Base):
        __tablename__ = "users"

        id = Column(Integer, primary_key=True)
        name = Column(String(length=16))


    class ReportView(BaseView):
        name = "Report Page"
        icon = "TrendingUp"

        @expose("/report", methods=["GET"])
        async def report_page(self, request):
            async with Session(expire_on_commit=False) as session:
                stmt = select(func.count(User.id))
                result = await session.execute(stmt)
                users_count = result.scalar_one()

            return JSONResponse({"users_count": users_count})


    admin.add_view(ReportView)

    ```

Now running your server you can head to `/admin/report` and see the user count.

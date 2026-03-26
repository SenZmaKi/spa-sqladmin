SQLAdmin now uses a React-based SPA for the admin interface. Rich text editing for textarea fields can be configured through the frontend components.

For textarea fields in your models, SQLAdmin will automatically render a `<Textarea>` component. If you need a WYSIWYG editor, you can customize the frontend by modifying the `FormField` component in `frontend/src/pages/create.tsx` to integrate a React-based rich text editor like [TipTap](https://tiptap.dev/) or [Lexical](https://lexical.dev/).

Let's say you have the following model:

```py
class Post(Base):
    id = Column(Integer, primary_key=True)
    content = Column(Text, nullable=False)
```

The `content` field will be rendered as a `textarea` in the admin create/edit forms. SQLAdmin's form schema API will report it as type `"textarea"`, which the React frontend renders accordingly.

For custom rich text integration, modify the `FieldInput` component in the frontend source to add a WYSIWYG editor for `textarea` type fields.

class CreatedByMixin:
    """
    Mixin to add a 'created_by' field to serializer context and auto-assign it on save.
    """
    def get_created_by_profile(self):
        user = getattr(self.request, 'user', None)
        if user and user.is_authenticated and hasattr(user, 'profile'):
            return user.profile
        return None

    def get_serializer_context(self):
        context = super().get_serializer_context()
        created_by = self.get_created_by_profile()
        if created_by:
            context['created_by'] = created_by
        return context

    def perform_create(self, serializer):
        created_by = self.get_created_by_profile()
        if created_by:
            serializer.save(created_by=created_by)
        else:
            serializer.save()

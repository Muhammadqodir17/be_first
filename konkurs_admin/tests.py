# from django.test import TestCase
# update comp
# comp = Competition.objects.filter(id=kwargs['pk']).first()
# if comp is None:
#     return Response(data={'error': 'Competition not found'}, status=status.HTTP_404_NOT_FOUND)
# serializer = CompetitionSerializer(comp, data=request.data, partial=True)
# if not serializer.is_valid():
#     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
# comp = serializer.save()
# if 'criteria' in request.data:
#     GradeCriteria.objects.filter(competition=comp).delete()
#     criteria = request.data.get('criteria', [])
#     for criteria_name in criteria:
#         GradeCriteria.objects.create(competition=comp, criteria=criteria_name)
# updated_serializer = CompetitionSerializer(comp)
# return Response(data=updated_serializer.data, status=status.HTTP_200_OK)

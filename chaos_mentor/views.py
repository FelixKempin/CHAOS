from django.shortcuts import render

# Create your views here.
from django.views import generic
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.views.decorators.http import require_POST

from .models import Goal, Advice, GoalStatusUpdate
from .forms import GoalForm, GoalStatusUpdateForm
from .services.mentor_service import evaluate_goal

class GoalListView(generic.ListView):
    model = Goal
    template_name = 'goal_list.html'
    context_object_name = 'goals'

class GoalDetailView(generic.DetailView):
    model = Goal
    template_name = 'goal_detail.html'
    context_object_name = 'goal'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        goal = self.object
        advices = Advice.objects.filter(goal=goal).order_by('-date')
        updates = GoalStatusUpdate.objects.filter(goal=goal).order_by('-date')

        timeline = sorted(
            [{"type": "advice", "entry": advice} for advice in advices] +
            [{"type": "status_update", "entry": update} for update in updates],
            key=lambda x: x["entry"].date,
            reverse=True
        )

        context["timeline"] = timeline
        context["status_form"] = GoalStatusUpdateForm(initial={"goal": goal})
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = GoalStatusUpdateForm(request.POST)
        if form.is_valid():
            status_update = form.save()
            evaluate_goal(str(self.object.pk))
            return redirect("goal_detail", pk=self.object.pk)
        context = self.get_context_data()
        context["status_form"] = form
        return self.render_to_response(context)

class GoalCreateView(generic.CreateView):
    model = Goal
    form_class = GoalForm
    template_name = 'goal_form.html'
    success_url = reverse_lazy('goal_list')

class GoalUpdateView(generic.UpdateView):
    model = Goal
    form_class = GoalForm
    template_name = 'goal_form.html'
    success_url = reverse_lazy('goal_list')

class GoalDeleteView(generic.DeleteView):
    model = Goal
    template_name = 'goal_confirm_delete.html'
    success_url = reverse_lazy('goal_list')


@require_POST
def delete_advice(request, pk):
    advice = get_object_or_404(Advice, pk=pk)
    goal_pk = advice.goal.pk
    advice.delete()
    return redirect(reverse("goal_detail", args=[goal_pk]))

@require_POST
def delete_status_update(request, pk):
    update = get_object_or_404(GoalStatusUpdate, pk=pk)
    goal_pk = update.goal.pk
    update.delete()
    return redirect(reverse("goal_detail", args=[goal_pk]))


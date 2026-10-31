hud title="Quest Tracker" anchor=top-right
row label=Kills value=12 of=20
row label=Deaths value=3 of=20
bar value=0.6 color=green
end
form id=grill-3 title="Confirm scope"
q choice id=q1 text="Delete cache?" options=yes|no|skip
q multi id=q2 text=Targets options=docs|code|tests
btn action=submit label=Go
btn action=cancel label=Abort
end

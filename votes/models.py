import uuid
from django.db import models
from elections.models.elections import Election
from elections.models.candidates import Candidate
from elections.models.positions import Position

class Vote(models.Model):
    voter_did_hash = models.CharField(max_length=64)
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name='votes')
    position = models.ForeignKey(Position, on_delete=models.CASCADE)
    election = models.ForeignKey(Election, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    receipt = models.CharField(max_length=128, unique=True, editable=False)
    tx_hash = models.CharField(max_length=66, blank=True, null=True)
    is_synced = models.BooleanField(default=False)  # Track if vote is synced to blockchain

    class Meta:
        unique_together = ('voter_did_hash', 'position')
        ordering = ['-timestamp']
        verbose_name = "Vote"
        verbose_name_plural = "Votes"

    def __str__(self):
        return f"Vote (receipt: {self.receipt})"

    def save(self, *args, **kwargs):
        if not self.receipt:
            self.receipt = uuid.uuid4().hex  # Or use SHA-based logic if needed
        super().save(*args, **kwargs)

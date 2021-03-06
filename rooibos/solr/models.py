from django.db import models
from django.db.models.signals import post_delete, post_save
from django.contrib.contenttypes.models import ContentType
from rooibos.data.models import Record, CollectionItem
from tagging.models import TaggedItem
from rooibos.util.models import OwnedWrapper
from workers import schedule_solr_index
import logging
from django.core.cache import cache


DELAY_INDEXING_CACHE_KEY = '_solr_delay_record_indexing'

# todo: remove logging from file? (not used)
log = logging.getLogger('rooibos')


class SolrIndexUpdates(models.Model):
    record = models.IntegerField()
    delete = models.BooleanField(default=False)

    class Meta:
        db_table = 'solr_solrindexupdates'


def mark_for_update(record_id, delete=False):
    SolrIndexUpdates.objects.create(record=record_id, delete=delete)
    delay = cache.get(DELAY_INDEXING_CACHE_KEY)
    if not delay:
        log.debug('Record indexing is not delayed, creating indexing job')
        schedule_solr_index()
    else:
        log.debug('Record indexing is delayed, not creating indexing job')


def delay_record_indexing():
    log.debug('Delaying record indexing')
    cache.set(DELAY_INDEXING_CACHE_KEY, True)

def resume_record_indexing():
    log.debug('Resuming record indexing')
    cache.set(DELAY_INDEXING_CACHE_KEY, False)
    schedule_solr_index()


def post_record_delete_callback(sender, **kwargs):
    mark_for_update(record_id=kwargs['instance'].id, delete=True)


def post_record_save_callback(sender, **kwargs):
    mark_for_update(record_id=kwargs['instance'].id)


def post_taggeditem_callback(sender, instance, **kwargs):
    owned_wrapper_type = ContentType.objects.get_for_model(OwnedWrapper)
    if instance and instance.content_type == owned_wrapper_type:
        instance = instance.object
        record_type = ContentType.objects.get_for_model(Record)
        if instance and instance.content_type == record_type:
            mark_for_update(record_id=instance.object_id)


def post_collectionitem_callback(sender, **kwargs):
    mark_for_update(record_id=kwargs['instance'].record.id)


post_delete.connect(post_record_delete_callback, sender=Record)
post_save.connect(post_record_save_callback, sender=Record)

post_delete.connect(post_taggeditem_callback, sender=TaggedItem)
post_save.connect(post_taggeditem_callback, sender=TaggedItem)

post_delete.connect(post_collectionitem_callback, sender=CollectionItem)
post_save.connect(post_collectionitem_callback, sender=CollectionItem)


def disconnect_signals():
    post_delete.disconnect(post_record_delete_callback, sender=Record)
    post_save.disconnect(post_record_save_callback, sender=Record)

    post_delete.disconnect(post_taggeditem_callback, sender=TaggedItem)
    post_save.disconnect(post_taggeditem_callback, sender=TaggedItem)

    post_delete.disconnect(post_collectionitem_callback, sender=CollectionItem)
    post_save.disconnect(post_collectionitem_callback, sender=CollectionItem)
